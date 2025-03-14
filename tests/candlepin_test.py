import re


def assert_secret_content(server, secret_name, secret_value):
    secret = server.run(f'podman secret inspect --format {"{{.SecretData}}"} --showsecret {secret_name}')
    assert secret.succeeded
    assert secret.stdout.strip() == secret_value


def test_candlepin_service(server):
    candlepin = server.service("candlepin")
    assert candlepin.is_running
    assert candlepin.is_enabled


def test_candlepin_port(server):
    candlepin = server.addr("localhost")
    assert candlepin.port("23443").is_reachable


def test_candlepin_status(server, certificates):
    status = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null --write-out '%{{http_code}}' https://localhost:23443/candlepin/status")
    assert status.succeeded
    assert status.stdout == '200'


def test_artemis_port(server):
    candlepin = server.addr("localhost")
    assert candlepin.port("61613").is_reachable


def test_artemis_auth(server, certificates):
    cmd = server.run(f'echo "" | openssl s_client -CAfile {certificates["ca_certificate"]} -cert {certificates["client_certificate"]} -key {certificates["client_key"]} -connect localhost:61613')
    assert cmd.succeeded, f"exit: {cmd.rc}\n\nstdout:\n{cmd.stdout}\n\nstderr:\n{cmd.stderr}"


def test_certs_users_file(server, certificates):
    cmd = server.run(f'openssl x509 -noout -subject -in {certificates["client_certificate"]} -nameopt rfc2253,sep_comma_plus_space')
    subject = cmd.stdout.replace("subject=", "").rstrip()
    assert_secret_content(server, 'candlepin-artemis-cert-users-properties', f'katelloUser={subject}')


def test_tls(server):
    result = server.run('nmap --script +ssl-enum-ciphers localhost -p 23443')
    result = result.stdout
    # We don't enable TLSv1.3 by default yet. TLSv1.3 support was added in tomcat 7.0.92
    # But tomcat 7.0.76 is the latest version available on EL7
    assert "TLSv1.3" not in result

    # Test that TLSv1.2 is enabled
    assert "TLSv1.2" in result

    # Test that older TLS versions are disabled
    assert "TLSv1.1" not in result
    assert "TLSv1.0" not in result

    # Test that the least cipher strength is "strong" or "A"
    assert "least strength: A" in result


def test_cert_roles(server):
    assert_secret_content(server, 'candlepin-artemis-cert-roles-properties', 'candlepinEventsConsumer=katelloUser')
