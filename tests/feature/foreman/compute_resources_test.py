import pytest


# TODO: Foreman really should have a dedicated API endpoint to expose this info
@pytest.fixture
def provider_description(foremanapi):
    create = foremanapi.resource('compute_resources').action('create')
    compute_resource_param = [param for param in create.params if param.name == 'compute_resource'][0]
    provider = [param for param in compute_resource_param.params if param.name == 'provider'][0]
    return provider.description


@pytest.mark.parametrize("compute_resource", ['EC2', 'Libvirt', 'Openstack', 'Vmware'])
def test_foreman_compute_resources_built_in(provider_description, compute_resource):
    assert compute_resource in provider_description


@pytest.mark.feature('azure-rm')
def test_foreman_compute_resources_azure_rm(provider_description):
    assert 'AzureRm' in provider_description


@pytest.mark.feature('google')
def test_foreman_compute_resources_google(provider_description):
    assert 'GCE' in provider_description
