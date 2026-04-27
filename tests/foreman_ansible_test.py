import json
import pytest

FOREMAN_PROXY_PORT = 8443
ROLE_NAME = "theforeman.foremanctltest"


def test_foreman_ansible_plugin_installed(foremanapi):
    plugins = [plugin['name'] for plugin in foremanapi.list('plugins')]
    assert 'foreman_ansible' in plugins


def test_foreman_proxy_ansible_feature(server, certificates, server_fqdn):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features")
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "ansible" in features


def test_import_ansible_role(ansible_role, server):
    role_list = server.run(f"hammer --output csv --no-headers ansible roles list --search='name={ansible_role}'")
    assert role_list.succeeded
    assert ansible_role in role_list.stdout


@pytest.fixture(scope="module")
def ansible_proxy_id(foremanapi):
    proxies = foremanapi.list('smart_proxies')
    for proxy in proxies:
        if any(f['name'] == 'Ansible' for f in proxy.get('features', [])):
            return proxy['id']
    pytest.skip("No smart proxy with Ansible feature found")


@pytest.fixture(scope="module")
def ansible_role(server, foremanapi, ansible_proxy_id):
    setup = server.run(f"mkdir -p /etc/ansible/roles/{ROLE_NAME}/tasks")
    assert setup.succeeded

    write = server.run(f"echo '- command: uptime' > /etc/ansible/roles/{ROLE_NAME}/tasks/main.yml")
    assert write.succeeded

    fetch = server.run(f"hammer ansible roles fetch --proxy-id {ansible_proxy_id}")
    assert fetch.succeeded

    sync = server.run(f"hammer ansible roles sync --proxy-id {ansible_proxy_id} --role-names {ROLE_NAME}")
    assert sync.succeeded

    for task in foremanapi.list('foreman_tasks', search='label ~ SyncRolesAndVariables and state != stopped'):
        foremanapi.wait_for_task(task)

    yield ROLE_NAME


def test_run_ansible_role(ansible_role, foremanapi, server, server_fqdn):
    assign = server.run(f"hammer host ansible-roles assign --name {server_fqdn} --ansible-roles {ansible_role}")
    assert assign.succeeded
    assert 'Ansible roles were assigned to the host' in assign.stdout

    play = server.run(f"hammer host ansible-roles play --name {server_fqdn}")
    assert play.succeeded
    assert 'Ansible roles are being played.' in play.stdout

    tasks = foremanapi.list('foreman_tasks', search='label = Actions::RemoteExecution::RunHostsJob')
    for task in tasks:
        foremanapi.wait_for_task(task)

    report = server.run(f"hammer --output csv --no-headers config-report list --search 'host={server_fqdn} origin=Ansible'")
    assert report.succeeded
    assert server_fqdn in report.stdout
    assert 'Ansible' in report.stdout


def test_run_command_via_ansible(foremanapi, server_fqdn):
    templates = foremanapi.list('job_templates', search='name = "Run Command - Ansible Default"')
    job = foremanapi.create('job_invocations', {
        'job_template_id': templates[0]['id'],
        'inputs': {'command': 'uptime'},
        'search_query': f'name = {server_fqdn}',
        'targeting_type': 'static_query',
    })
    task = foremanapi.wait_for_task(job['task'])
    assert task['result'] == 'success'
