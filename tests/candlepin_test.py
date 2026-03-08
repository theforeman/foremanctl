
def assert_secret_content(server, secret_name, secret_value):
    secret = server.run(f'podman secret inspect --format {"{{.SecretData}}"} --showsecret {secret_name}')
    assert secret.succeeded
    assert secret.stdout.strip() == secret_value


def test_candlepin_service(server):
    candlepin = server.service("candlepin")
    assert candlepin.is_running


def test_candlepin_status(server):
    status = server.run("podman exec foreman curl --cacert /etc/foreman/katello-default-ca.crt --silent --output /dev/null --write-out '%{http_code}' https://candlepin:23443/candlepin/status")
    assert status.succeeded
    assert status.stdout == '200'


def test_artemis_auth(server):
    cmd = server.run('podman exec foreman bash -c \'echo "" | openssl s_client -CAfile /etc/foreman/katello-default-ca.crt -cert /etc/foreman/client_cert.pem -key /etc/foreman/client_key.pem -connect candlepin:61613 -servername candlepin\'')
    assert cmd.succeeded, f"exit: {cmd.rc}\n\nstdout:\n{cmd.stdout}\n\nstderr:\n{cmd.stderr}"


def test_certs_users_file(server, certificates):
    cmd = server.run(f'openssl x509 -noout -subject -in {certificates["client_certificate"]} -nameopt rfc2253,sep_comma_plus_space')
    subject = cmd.stdout.replace("subject=", "").rstrip()
    assert_secret_content(server, 'candlepin-artemis-cert-users-properties', f'katelloUser={subject}')


def test_tls(server):
    ca = '/etc/foreman/katello-default-ca.crt'

    # TLSv1.2 should be enabled
    result = server.run(f'podman exec foreman bash -c "echo Q | openssl s_client -connect candlepin:23443 -tls1_2 -CAfile {ca} 2>&1"')
    assert "Cipher is" in result.stdout, f"TLSv1.2 not available:\n{result.stdout}"

    # TLSv1.3, TLSv1.1 and TLSv1.0 should be disabled
    for flag in ['-tls1_3', '-tls1_1', '-tls1']:
        result = server.run(f'podman exec foreman bash -c "echo Q | openssl s_client -connect candlepin:23443 {flag} -CAfile {ca} 2>&1"')
        assert result.rc != 0, f"TLS version ({flag}) should be disabled:\n{result.stdout}"


def test_cert_roles(server):
    assert_secret_content(server, 'candlepin-artemis-cert-roles-properties', 'candlepinEventsConsumer=katelloUser')
