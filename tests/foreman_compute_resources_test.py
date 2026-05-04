import pytest

from conftest import has_feature

pytestmark = pytest.mark.skipif(
    not has_feature("hammer"),
    reason="hammer not enabled",
)

FOREMAN_HOST = 'localhost'
FOREMAN_PORT = 3000

@pytest.mark.parametrize("compute_resource", [
    pytest.param('AzureRm', marks=pytest.mark.skipif(not has_feature('azure-rm'), reason="azure-rm not enabled")),
    pytest.param('EC2'),
    pytest.param('GCE', marks=pytest.mark.skipif(not has_feature('google'), reason="google not enabled")),
    pytest.param('Libvirt'),
    pytest.param('Openstack'),
    pytest.param('Vmware'),
])
def test_foreman_compute_resources(server, compute_resource):
    hammer = server.run("hammer compute-resource create --help | grep provider")
    assert hammer.succeeded
    assert compute_resource in hammer.stdout
