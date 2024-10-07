HTTP_HOST = 'localhost'
HTTP_PORT = 80
HTTPS_PORT = 443


def test_httpd_service(host):
    httpd = host.service("httpd")
    assert httpd.is_running
    assert httpd.is_enabled


def test_http_port(host):
    httpd = host.addr(HTTP_HOST)
    assert httpd.port(HTTP_PORT).is_reachable


def test_https_port(host):
    httpd = host.addr(HTTP_HOST)
    assert httpd.port(HTTPS_PORT).is_reachable


def test_https_foreman_ping(host):
    cmd = host.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/api/v2/ping')
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_status(host):
    cmd = host.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/pulp/api/v3/status/')
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_content(host):
    cmd = host.run('curl --cacert /root/certificates/certs/ca.crt --silent --output /dev/null --write-out \'%{http_code}\' https://quadlet.example.com/pulp/content/')
    assert cmd.succeeded
    assert cmd.stdout == '200'
