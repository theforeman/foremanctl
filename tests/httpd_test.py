HTTP_HOST = 'localhost'
HTTP_PORT = 80
HTTPS_PORT = 443


def test_httpd_service(server):
    httpd = server.service("httpd")
    assert httpd.is_running
    assert httpd.is_enabled


def test_http_port(server):
    httpd = server.addr(HTTP_HOST)
    assert httpd.port(HTTP_PORT).is_reachable


def test_https_port(server):
    httpd = server.addr(HTTP_HOST)
    assert httpd.port(HTTPS_PORT).is_reachable


def test_https_foreman_ping(server):
    cmd = server.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/api/v2/ping')
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_status(server):
    cmd = server.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/pulp/api/v3/status/')
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_content(server):
    cmd = server.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/pulp/content/')
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_auth(server):
    cmd = server.run(f"curl --cacert /root/certificates/certs/ca.crt --silent --write-out '%{{stderr}}%{{http_code}}' --cert /root/certificates/certs/quadlet.example.com-client.crt --key /root/certificates/private/quadlet.example.com-client.key https://quadlet.example.com/pulp/api/v3/users/")
    assert cmd.succeeded
    assert cmd.stderr == '200'
