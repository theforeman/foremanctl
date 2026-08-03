def assert_secret_content(server, secret_name, secret_value):
    secret = server.run(f'podman secret inspect --format {"{{.SecretData}}"} --showsecret {secret_name}')
    assert secret.succeeded
    assert secret.stdout.strip() == secret_value


def test_candlepin_service(server):
    candlepin = server.service("candlepin")
    assert candlepin.is_running


def test_candlepin_runs_as_tomcat(server):
    assert server.run("podman exec candlepin id -un").stdout.strip() == 'tomcat'
    assert server.run("podman exec candlepin id -u").stdout.strip() != '0'

    groups = server.run("podman exec candlepin id -Gn").stdout.split()
    assert 'tomcat' in groups
    assert 'root' not in groups

    assert server.run("podman exec candlepin test -r /etc/candlepin/certs/tomcat.key").succeeded
    assert server.run("podman exec candlepin test -r /etc/tomcat/tomcat.conf").succeeded

    secret_ownership = server.run(
        "podman exec candlepin stat -c '%U:%G %a' /etc/candlepin/certs/tomcat.key"
    ).stdout.strip()
    assert secret_ownership == 'root:tomcat 440'


def test_candlepin_port(server):
    candlepin = server.addr("localhost")
    assert candlepin.port("23443").is_reachable


def test_candlepin_status(server, certificates):
    status = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null --write-out '%{{http_code}}' https://localhost:23443/candlepin/status")
    assert status.succeeded
    assert status.stdout == '200'


def test_candlepin_logs_in_journal(server, certificates):
    server.run(
        f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null "
        f"https://localhost:23443/candlepin/status"
    )

    journal = server.run("journalctl -u candlepin --since '2 min ago' --no-pager").stdout
    assert 'candlepin/status' in journal
    assert 'LoggingFilter' in journal


def test_candlepin_tomcat_logs_in_journal(server, certificates):
    server.run(
        f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null "
        f"https://localhost:23443/candlepin/status"
    )

    journal = server.run("journalctl -u candlepin --no-pager").stdout
    assert '"GET /candlepin/status HTTP/1.1"' in journal
    assert 'org.apache.catalina' in journal


def test_tls(server):
    def tls_supported(flag):
        result = server.run(f'echo | openssl s_client -connect localhost:23443 {flag} 2>&1')
        return 'Cipher is' in result.stdout and '(NONE)' not in result.stdout

    assert tls_supported('-tls1_3')
    assert tls_supported('-tls1_2')
    assert not tls_supported('-tls1_1')
    assert not tls_supported('-tls1')

    # Verify only strong (AEAD) ciphers are negotiated
    result = server.run('echo | openssl s_client -connect localhost:23443 -tls1_2 2>&1')
    assert 'GCM' in result.stdout
