import pytest


@pytest.fixture
def foreman_plugins(foremanapi):
    return [plugin['name'] for plugin in foremanapi.list('plugins')]


@pytest.mark.feature('azure-rm')
def test_foreman_compute_resources_azure_rm(foreman_plugins):
    assert 'foreman_azure_rm' in foreman_plugins


@pytest.mark.feature('google')
def test_foreman_compute_resources_google(foreman_plugins):
    assert 'foreman_google' in foreman_plugins


@pytest.mark.feature('webhooks')
def test_foreman_webhooks(foreman_plugins):
    assert 'foreman_webhooks' in foreman_plugins
