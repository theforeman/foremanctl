def test_foreman_content_view(client_environment, activation_key, organization, foremanapi, client):
    client.run('dnf install -y subscription-manager')
    rcmd = foremanapi.create('registration_commands', {'organization_id': organization['id'], 'insecure': True, 'activation_keys': [activation_key['name']]})
    client.run_test(rcmd['registration_command'])
    client.run('subscription-manager repos --enable=*')
    client.run_test('dnf install -y bear')
    assert client.package('bear').is_installed
    client.run('dnf remove -y bear')
    client.run('subscription-manager unregister')
    client.run('subscription-manager clean')
