import pytest

FOREMAN_HOST = 'localhost'
FOREMAN_PORT = 3000

@pytest.mark.parametrize("compute_resource", [
    pytest.param('AzureRm', marks=pytest.mark.feature('azure-rm')),
    pytest.param('EC2'),
    pytest.param('GCE', marks=pytest.mark.feature('google')),
    pytest.param('Libvirt'),
    pytest.param('Openstack'),
    pytest.param('Vmware'),
])
def test_foreman_compute_resources(server, compute_resource):
    hammer = server.run("hammer compute-resource create --help | grep provider")
    assert hammer.succeeded
    assert compute_resource in hammer.stdout
