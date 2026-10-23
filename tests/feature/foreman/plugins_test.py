import pytest


@pytest.mark.feature('azure-rm')
def test_foreman_compute_resources_azure_rm(foreman_plugins):
    assert 'foreman_azure_rm' in foreman_plugins


@pytest.mark.feature('google')
def test_foreman_compute_resources_google(foreman_plugins):
    assert 'foreman_google' in foreman_plugins


@pytest.mark.feature('virt-who')
def test_foreman_virt_who(foreman_plugins):
    assert 'foreman_virt_who_configure' in foreman_plugins
