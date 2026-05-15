import subprocess
import uuid
from functools import cached_property

import apypie
import paramiko
import py.path
import pytest
import requests
import testinfra
import yaml
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from requests.adapters import HTTPAdapter

SSH_CONFIG = './.tmp/ssh-config'


class UserParameters:
    def __init__(self, config):
        self._config = config

    @cached_property
    def features(self):
        # foremanctl outputs
        # FEATURE                   STATE               DESCRIPTION
        # $feature                  enabled/available   $description
        output = subprocess.check_output(['./foremanctl', 'features'], cwd=self._config.rootdir,
                                         universal_newlines=True)
        lines = output.splitlines(keepends=False)
        # feature, status, description
        return [line.split(None, 2) for line in lines[1:]]

    @cached_property
    def available_features(self):
        return set(feature for feature, _status, _desc in self.features)

    @cached_property
    def enabled_features(self):
        return set(feature for feature, status, _desc in self.features if status == 'enabled')


def pytest_addoption(parser):
    parser.addoption("--certificate-source", action="store", default="default", choices=('default', 'installer', 'custom_server'), help="Certificate source used during deployment")
    parser.addoption("--database-mode", action="store", default="internal", choices=('internal', 'external'), help="Whether the database is internal or external")


@pytest.fixture(scope="module")
def enabled_features(pytestconfig):
    return pytestconfig.user_parameters.enabled_features


@pytest.fixture(scope="module")
def fixture_dir():
    return py.path.local(__file__).realpath() / '..' / 'fixtures'


@pytest.fixture(scope="module")
def server_hostname():
    return 'quadlet'


@pytest.fixture(scope="module")
def server_fqdn(server):
    return server.check_output('hostname -f')


@pytest.fixture(scope="module")
def client_hostname():
    return 'client'


@pytest.fixture(scope="module")
def client_fqdn(client):
    return client.check_output('hostname -f')


@pytest.fixture(scope="module")
def certificates(certificate_source, server_fqdn):
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template(f"./src/vars/{certificate_source}_certificates.yml")
    context = {'certificates_ca_directory': '/var/lib/foremanctl/certs',
               'ansible_facts': {'fqdn': server_fqdn}}
    # we have vars that refer to other vars, so load them once and then re-render the template
    context.update(yaml.safe_load(template.render(context)))
    return yaml.safe_load(template.render(context))


@pytest.fixture(scope="module")
def certificate_source(pytestconfig):
    return pytestconfig.getoption("certificate_source")


@pytest.fixture(scope="module")
def custom_certificates(certificate_source):
    if certificate_source != 'custom_server':
        pytest.skip("Only applies to custom certificate deployments")


@pytest.fixture(scope="module")
def default_certificates(certificate_source):
    if certificate_source == 'custom_server':
        pytest.skip("Only applies to non-custom certificate deployments")


@pytest.fixture(scope="module")
def database_mode(pytestconfig):
    return pytestconfig.getoption("database_mode")


@pytest.fixture(scope="module")
def server(server_hostname):
    yield testinfra.get_host(f'paramiko://{server_hostname}', sudo=True, ssh_config=SSH_CONFIG)


@pytest.fixture(scope="module")
def client(client_hostname):
    yield testinfra.get_host(f'paramiko://{client_hostname}', sudo=True, ssh_config=SSH_CONFIG)


@pytest.fixture(scope="module")
def database(database_mode, server):
    if database_mode == 'external':
        yield testinfra.get_host('paramiko://database', sudo=True, ssh_config=SSH_CONFIG)
    else:
        yield server


@pytest.fixture(scope="module")
def ssh_config(server_hostname):
    config = paramiko.SSHConfig.from_path(SSH_CONFIG)
    return config.lookup(server_hostname)


@pytest.fixture(scope="module")
def foremanapi(ssh_config, server_fqdn):
    api = apypie.ForemanApi(
        uri=f'https://{ssh_config["hostname"]}',
        username='admin',
        password='changeme',
        verify_ssl=False,
    )
    api._session.headers['Host'] = server_fqdn
    return api


@pytest.fixture
def organization(foremanapi):
    org = foremanapi.create('organizations', {'name': str(uuid.uuid4())})
    yield org
    foremanapi.delete('organizations', org)


@pytest.fixture
def product(organization, foremanapi):
    prod = foremanapi.create('products', {'name': str(uuid.uuid4()), 'organization_id': organization['id']})
    yield prod
    foremanapi.delete('products', prod)


@pytest.fixture
def yum_repository(product, organization, foremanapi):
    repo = foremanapi.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'yum', 'url': 'https://fixtures.pulpproject.org/rpm-no-comps/'})
    wait_for_metadata_generate(foremanapi)
    yield repo
    foremanapi.delete('repositories', repo)


@pytest.fixture
def file_repository(product, organization, foremanapi):
    repo = foremanapi.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'file', 'url': 'https://fixtures.pulpproject.org/file/'})
    wait_for_metadata_generate(foremanapi)
    yield repo
    foremanapi.delete('repositories', repo)


@pytest.fixture
def container_repository(product, organization, foremanapi):
    repo = foremanapi.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'docker', 'url': 'https://quay.io/', 'docker_upstream_name': 'foreman/busybox-test'})
    wait_for_metadata_generate(foremanapi)
    yield repo
    foremanapi.delete('repositories', repo)


@pytest.fixture
def lifecycle_environment(organization, foremanapi):
    library = foremanapi.list('lifecycle_environments', 'name=Library', {'organization_id': organization['id']})[0]
    lce = foremanapi.create('lifecycle_environments', {'name': str(uuid.uuid4()), 'organization_id': organization['id'], 'prior_id': library['id']})
    yield lce
    foremanapi.delete('lifecycle_environments', lce)


@pytest.fixture
def content_view(organization, foremanapi):
    cv = foremanapi.create('content_views', {'name': str(uuid.uuid4()), 'organization_id': organization['id']})
    yield cv
    foremanapi.delete('content_views', cv)


@pytest.fixture
def activation_key(organization, foremanapi):
    ak = foremanapi.create('activation_keys', {'name': str(uuid.uuid4()), 'organization_id': organization['id']})
    yield ak
    foremanapi.delete('activation_keys', ak)


@pytest.fixture
def client_environment(activation_key, content_view, lifecycle_environment, yum_repository, organization, foremanapi):
    foremanapi.resource_action('repositories', 'sync', {'id': yum_repository['id']})
    foremanapi.update('content_views', {'id': content_view['id'], 'repository_ids': [yum_repository['id']]})
    foremanapi.resource_action('content_views', 'publish', {'id': content_view['id']})

    library = foremanapi.list('lifecycle_environments', 'name=Library', {'organization_id': organization['id']})[0]
    foremanapi.update('activation_keys', {'id': activation_key['id'], 'organization_id': organization['id'], 'environment_id': library['id'], 'content_view_id': content_view['id']})

    yield activation_key

    foremanapi.update('activation_keys', {'id': activation_key['id'], 'organization_id': organization['id'], 'environment_id': None, 'content_view_id': None})

    versions = foremanapi.list('content_view_versions', params={'content_view_id': content_view['id']})
    for version in versions:
        current_environment_ids = {environment['id'] for environment in version['environments']}
        for environment_id in current_environment_ids:
            foremanapi.resource_action('content_views', 'remove_from_environment', params={'id': content_view['id'], 'environment_id': environment_id})
        foremanapi.delete('content_view_versions', version)


def wait_for_tasks(foremanapi, search=None):
    tasks = foremanapi.list('foreman_tasks', search=search)
    for task in tasks:
        foremanapi.wait_for_task(task)


def wait_for_metadata_generate(foremanapi):
    wait_for_tasks(foremanapi, 'label = Actions::Katello::Repository::MetadataGenerate')


def pytest_configure(config):
    config.addinivalue_line("markers", "feature(name): mark a test as requiring a feature")

    config.user_parameters = UserParameters(config)


def pytest_collection_modifyitems(config, items):
    feature_dir = config.rootdir / 'tests' / 'feature'
    for item in items:
        try:
            rel_path = item.path.relative_to(feature_dir)
        except ValueError:
            # Not in the features directory
            pass
        else:
            feature = rel_path.parts[0]
            item.add_marker(pytest.mark.feature(feature))


def pytest_runtest_setup(item):
    feature_markers = set(mark.args[0] for mark in item.iter_markers(name="feature"))
    if feature_markers:
        invalid_features = feature_markers - item.config.user_parameters.available_features
        if invalid_features:
            raise pytest.PytestConfigWarning(f"Invalid feature(s) {invalid_features!r} on {item}")
        missing = feature_markers - item.config.user_parameters.enabled_features
        if missing:
            pytest.skip(f"test requires feature(s) {missing!r}")


class ResolveAdapter(HTTPAdapter):
    def __init__(self, target_ip, *args, **kwargs):
        self.target_ip = target_ip
        super().__init__(*args, **kwargs)

    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        conn = super().get_connection_with_tls_context(request, verify, proxies, cert)

        # Override the host to point to your target IP
        # This forces the socket to open to target_ip instead of the URL's domain
        conn.host = self.target_ip

        return conn


@pytest.fixture(scope="module")
def local_request(ssh_config, server_fqdn):
    session = requests.Session()
    adapter = ResolveAdapter(target_ip=ssh_config["hostname"])
    session.mount(f"http://{server_fqdn}", adapter)
    session.mount(f"https://{server_fqdn}", adapter)
    return session
