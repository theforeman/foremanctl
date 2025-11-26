import pytest

FOREMAN_HOST = 'localhost'
FOREMAN_PORT = 3000

@pytest.mark.parametrize("compute_resource", ['AzureRm', 'EC2', 'GCE', 'Libvirt', 'Openstack', 'Vmware'])
def test_foreman_compute_resources(server, compute_resource):
    hammer = server.run("hammer compute-resource create --help | grep provider")
    assert hammer.succeeded
    assert compute_resource in hammer.stdout
