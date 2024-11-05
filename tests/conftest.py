import uuid

import apypie
import paramiko
import pytest


@pytest.fixture(scope="module")
def ssh_config():
    config = paramiko.SSHConfig.from_path('./.vagrant/ssh-config')
    return config.lookup('quadlet')


@pytest.fixture(scope="module")
def foremanapi(ssh_config):
    return apypie.ForemanApi(
        uri=f'https://{ssh_config['hostname']}',
        username='admin',
        password='changeme',
        verify_ssl=False,
    )

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
    yield repo
    foremanapi.delete('repositories', repo)

@pytest.fixture
def file_repository(product, organization, foremanapi):
    repo = foremanapi.create('repositories', {'name': str(uuid.uuid4()), 'product_id': product['id'], 'content_type': 'file', 'url': 'https://fixtures.pulpproject.org/file/'})
    yield repo
    foremanapi.delete('repositories', repo)
