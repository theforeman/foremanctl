def assert_secret_content(server, secret_name, secret_value):
    secret = server.run(f'podman secret inspect --format {"{{.SecretData}}"} --showsecret {secret_name}')
    assert secret.succeeded
    assert secret.stdout.strip() == secret_value


def run_candlepin_status_from_foreman(server):
    return server.run(
        "podman exec foreman curl "
        "--cacert /etc/foreman/katello-default-ca.crt "
        "--noproxy candlepin "
        "--silent --output /dev/null --write-out '%{http_code}' "
        "https://candlepin:23443/candlepin/status"
    )


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


def test_candlepin_port_not_published(server):
    candlepin = server.addr("localhost")
    assert not candlepin.port("23443").is_reachable


def test_candlepin_status(server):
    status = run_candlepin_status_from_foreman(server)
    assert status.succeeded
    assert status.stdout == '200'


def test_candlepin_logs_in_journal(server):
    run_candlepin_status_from_foreman(server)

    journal = server.run("journalctl -u candlepin --since '2 min ago' --no-pager").stdout
    assert 'candlepin/status' in journal
    assert 'LoggingFilter' in journal


def test_candlepin_tomcat_logs_in_journal(server):
    run_candlepin_status_from_foreman(server)

    journal = server.run("journalctl -u candlepin --no-pager").stdout
    assert '"GET /candlepin/status HTTP/1.1"' in journal
    assert 'org.apache.catalina' in journal


def test_tls(server):
    for flag in ("-tls1_2", "-tls1_3"):
        result = server.run(
            "podman exec foreman bash -lc "
            f"\"echo Q | openssl s_client -connect candlepin:23443 -servername candlepin {flag} "
            "-CAfile /etc/foreman/katello-default-ca.crt 2>&1\""
        )
        assert result.succeeded
        assert "Verify return code: 0 (ok)" in result.stdout

    for flag in ("-tls1_1", "-tls1"):
        result = server.run(
            "podman exec foreman bash -lc "
            f"\"echo Q | openssl s_client -connect candlepin:23443 -servername candlepin {flag} "
            "-CAfile /etc/foreman/katello-default-ca.crt 2>&1\""
        )
        assert result.failed
        assert "no protocols available" in result.stdout
        assert "no peer certificate available" in result.stdout
