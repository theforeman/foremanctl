import pytest

from conftest import has_feature

@pytest.mark.parametrize("foreman_plugin", [
    pytest.param('foreman_azure_rm', marks=pytest.mark.skipif(not has_feature('azure-rm'), reason="azure-rm not enabled")),
    pytest.param('foreman_google', marks=pytest.mark.skipif(not has_feature('google'), reason="google not enabled")),
])
def test_foreman_compute_resources(foremanapi, foreman_plugin):
    plugins = [plugin['name'] for plugin in foremanapi.list('plugins')]
    assert foreman_plugin in plugins
