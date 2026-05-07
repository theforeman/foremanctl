import pytest

@pytest.mark.parametrize("foreman_plugin", ['foreman_ansible', 'foreman_azure_rm', 'foreman_google'])
def test_foreman_plugin_loaded(foremanapi, foreman_plugin):
    plugins = [plugin['name'] for plugin in foremanapi.list('plugins')]
    assert foreman_plugin in plugins

def test_ansible_default_job_template(foremanapi):
    templates = foremanapi.list('job_templates', search='name="Run Command - Ansible Default"')
    assert len(templates) > 0
