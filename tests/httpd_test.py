HTTP_HOST = 'localhost'
HTTP_PORT = 80
HTTPS_PORT = 443
HTTPD_PUB_DIR = '/var/www/html/pub'
CURL_CMD = "curl --silent --output /dev/null"

def test_httpd_service(server):
    if server.system_info.distribution == 'debian':
        service_name = 'apache2'
    else:
        service_name = 'httpd'
    httpd = server.service(service_name)
    assert httpd.is_running
    assert httpd.is_enabled

def test_http_port(server):
    httpd = server.addr(HTTP_HOST)
    assert httpd.port(HTTP_PORT).is_reachable

def test_https_port(server):
    httpd = server.addr(HTTP_HOST)
    assert httpd.port(HTTPS_PORT).is_reachable

def test_http_foreman_ping(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{redirect_url}}' http://{server_fqdn}/api/v2/ping")
    assert cmd.succeeded
    assert cmd.stdout == f'https://{server_fqdn}/api/v2/ping'

def test_https_foreman_ping(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/api/v2/ping")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_http_pulp_api_status(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '404'

def test_https_pulp_api_status(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_http_pulp_content(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{stderr}}%{{http_code}}' http://{server_fqdn}/pulp/content/")
    assert cmd.succeeded
    assert cmd.stderr == '200'

def test_https_pulp_content(server, certificates, server_fqdn):
    cmd = server.run(f"curl --silent --cacert {certificates['ca_certificate']} https://{server_fqdn}/pulp/content/")
    assert cmd.succeeded
    assert "Index of /pulp/content/" in cmd.stdout

def test_https_pulp_auth(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' --cert {certificates['client_certificate']} --key {certificates['client_key']} https://{server_fqdn}/pulp/api/v3/users/")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_pub_directory_exists(server):
    pub_dir = server.file(HTTPD_PUB_DIR)
    assert pub_dir.exists
    assert pub_dir.is_directory
    assert pub_dir.mode == 0o755

def test_http_pub_directory_accessible(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/pub/")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_https_pub_directory_accessible(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/pub/")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_http_pub_ca_certificate_downloadable(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/pub/katello-server-ca.crt")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_https_pub_ca_certificate_downloadable(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/pub/katello-server-ca.crt")
    assert cmd.succeeded
    assert cmd.stdout == '200'

def test_http_foreman_login(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/users/login")
    assert cmd.succeeded
    assert cmd.stdout == '301'

def test_https_foreman_login(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/users/login")
    assert cmd.succeeded
    assert cmd.stdout == '200'
