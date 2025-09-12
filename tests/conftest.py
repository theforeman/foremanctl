import uuid

import apypie
import paramiko
import pytest
import testinfra
import yaml

from jinja2 import Environment, FileSystemLoader, select_autoescape


VAGRANT_SSH_CONFIG='./.vagrant/ssh-config'


def pytest_addoption(parser):
    parser.addoption("--certificate-source", action="store", default="default", choices=('default', 'installer'), help="Where to obtain certificates from")


@pytest.fixture(scope="module")
def server_hostname():
    return 'quadlet'


@pytest.fixture(scope="module")
def server_fqdn(server_hostname):
    return f'{server_hostname}.example.com'


@pytest.fixture(scope="module")
def certificates(pytestconfig, server_fqdn):
    source = pytestconfig.getoption("certificate_source")
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template = env.get_template(f"./src/vars/{source}_certificates.yml")
    context = {'certificates_ca_directory': '/root/certificates',
               'ansible_fqdn': server_fqdn}
    return yaml.safe_load(template.render(context))


@pytest.fixture(scope="module")
def server(server_hostname):
    yield testinfra.get_host(f'paramiko://{server_hostname}', sudo=True, ssh_config=VAGRANT_SSH_CONFIG)


@pytest.fixture(scope="module")
def client():
    yield testinfra.get_host('paramiko://client', sudo=True, ssh_config=VAGRANT_SSH_CONFIG)


@pytest.fixture(scope="module")
def ssh_config(server_hostname):
    config = paramiko.SSHConfig.from_path(VAGRANT_SSH_CONFIG)
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
