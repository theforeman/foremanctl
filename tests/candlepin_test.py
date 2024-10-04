import re


def test_candlepin_service(host):
    candlepin = host.service("candlepin")
    assert candlepin.is_running
    assert candlepin.is_enabled


def test_candlepin_port(host):
    candlepin = host.addr("localhost")
    assert candlepin.port("23443").is_reachable


def test_candlepin_status(host):
    status = host.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://localhost:23443/candlepin/status')
    assert status.succeeded
    assert status.stdout == '200'


def test_artemis_port(host):
    candlepin = host.addr("localhost")
    assert candlepin.port("61613").is_reachable


def test_artemis_auth(host):
    cmd = host.run('echo "" | openssl s_client -CAfile /root/certificates/certs/ca.crt -cert /root/certificates/certs/quadlet.example.com-client.crt -key /root/certificates/private/quadlet.example.com-client.key -connect localhost:61613')
    assert cmd.succeeded, f"exit: {cmd.rc}\n\nstdout:\n{cmd.stdout}\n\nstderr:\n{cmd.stderr}"


def test_certs_users_file(host):
    file = host.file("/etc/tomcat/cert-users.properties")
    assert file.exists
    assert file.is_file
    assert file.mode == 0o640
    assert file.user == 'root'
    assert file.group == 'tomcat'


def test_tls(host):
    result = host.run('nmap --script +ssl-enum-ciphers localhost -p 23443')
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


def test_cert_roles(host):
    file = host.file('/etc/tomcat/cert-roles.properties')
    assert file.exists
    assert file.is_file
    assert file.mode == 0o640
    assert file.user == 'root'
    assert file.group == 'tomcat'
    assert file.contains('candlepinEventsConsumer=katelloUser')
