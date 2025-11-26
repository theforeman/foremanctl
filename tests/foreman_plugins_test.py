import pytest

@pytest.mark.parametrize("foreman_plugin", ['foreman_azure_rm', 'foreman_google'])
def test_foreman_compute_resources(foremanapi, foreman_plugin):
    plugins = [plugin['name'] for plugin in foremanapi.list('plugins')]
    assert foreman_plugin in plugins
