import pytest

@pytest.mark.parametrize("foreman_plugin", [
    pytest.param('foreman_azure_rm', marks=pytest.mark.feature('azure-rm')),
    pytest.param('foreman_google', marks=pytest.mark.feature('google')),
])
def test_foreman_compute_resources(foremanapi, foreman_plugin):
    plugins = [plugin['name'] for plugin in foremanapi.list('plugins')]
    assert foreman_plugin in plugins
