import pytest

pytestmark = pytest.mark.feature('foreman')


@pytest.mark.parametrize("compute_resource", ['AzureRm', 'EC2', 'GCE', 'Libvirt', 'Openstack', 'Vmware'])
def test_foreman_compute_resources(foremanapi, compute_resource):
    create = foremanapi.resource('compute_resources').action('create')
    compute_resource_param = [param for param in create.params if param.name == 'compute_resource'][0]
    provider = [param for param in compute_resource_param.params if param.name == 'provider'][0]
    assert compute_resource in provider.description
