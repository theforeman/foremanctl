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


def test_https_foreman_ping(server, certificates, server_hostname):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null --write-out '%{{http_code}}' https://{server_hostname}/api/v2/ping")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_status(server, certificates, server_hostname):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null --write-out '%{{http_code}}' https://{server_hostname}/pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_content(server, certificates, server_hostname):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --output /dev/null --write-out '%{{http_code}}' https://{server_hostname}/pulp/content/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulp_auth(server, certificates, server_hostname):
    cmd = server.run(f"curl --cacert {certificates['ca_certificate']} --silent --write-out '%{{stderr}}%{{http_code}}' --cert {certificates['client_certificate']} --key {certificates['client_key']} https://{server_hostname}/pulp/api/v3/users/")
    assert cmd.succeeded
    assert cmd.stderr == '200'
