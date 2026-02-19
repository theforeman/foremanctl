def test_foreman_content_view(client_environment, activation_key, organization, foremanapi, client):
    client.run('dnf install -y subscription-manager')
    rcmd = foremanapi.create('registration_commands', {'organization_id': organization['id'], 'insecure': True, 'activation_keys': [activation_key['name']], 'force': True})
    client.run_test(rcmd['registration_command'])
    client.run('subscription-manager repos --enable=*')
    client.run_test('dnf install -y bear')
    assert client.package('bear').is_installed
    client.run('dnf remove -y bear')
    client.run('subscription-manager unregister')
    client.run('subscription-manager clean')

def test_foreman_rex(client_environment, activation_key, organization, foremanapi, client, client_fqdn):
    client.run('dnf install -y subscription-manager')
    rcmd = foremanapi.create('registration_commands', {'organization_id': organization['id'], 'insecure': True, 'activation_keys': [activation_key['name']], 'force': True})
    client.run_test(rcmd['registration_command'])
    job = foremanapi.create('job_invocations', {'feature': 'run_script', 'inputs': {'command': 'uptime'}, 'search_query': f'name = {client_fqdn}', 'targeting_type': 'static_query'})
    task = foremanapi.wait_for_task(job['task'])
    assert task['result'] == 'success'
    foremanapi.delete('hosts', {'id': client_fqdn})
