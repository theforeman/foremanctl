def test_foreman_content_view(client_registration, client):
    client.run('subscription-manager repos --enable=*')
    client.run_test('dnf install -y bear')
    assert client.package('bear').is_installed
    client.run('dnf remove -y bear')


def test_foreman_rex(client_registration, foremanapi, client_fqdn):
    job = foremanapi.create('job_invocations', {'feature': 'run_script', 'inputs': {'command': 'uptime'}, 'search_query': f'name = {client_fqdn}', 'targeting_type': 'static_query'})
    task = foremanapi.wait_for_task(job['task'])
    assert task['result'] == 'success'
    foremanapi.delete('hosts', {'id': client_fqdn})
