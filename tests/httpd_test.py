import pytest

HTTP_HOST = 'localhost'
HTTP_PORT = 80
HTTPS_PORT = 443
HTTPD_PUB_DIR = '/var/www/html/pub'
CURL_CMD = "curl --silent --output /dev/null"


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


@pytest.mark.feature('foreman')
def test_http_foreman_ping(curl_request):
    cmd = curl_request("api/v2/ping")
    assert cmd.succeeded
    assert cmd.stdout == '200'


@pytest.mark.feature('foreman')
def test_https_foreman_ping(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['server_ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/api/v2/ping")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_http_pulp_api_status(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '404'


def test_https_pulp_api_status(server, certificates, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --cacert {certificates['server_ca_certificate']} --write-out '%{{http_code}}' https://{server_fqdn}/pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_http_pulp_content(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{stderr}}%{{http_code}}' http://{server_fqdn}/pulp/content/")
    assert cmd.succeeded
    assert cmd.stderr == '200'


def test_https_pulp_content(server, certificates, server_fqdn):
    cmd = server.run(f"curl --silent --cacert {certificates['server_ca_certificate']} https://{server_fqdn}/pulp/content/")
    assert cmd.succeeded
    assert "Index of /pulp/content/" in cmd.stdout


def test_https_pulp_auth(curl_request):
    cmd = curl_request("pulp/api/v3/users/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pypi_endpoint(curl_request):
    cmd = curl_request("pypi/test/", return_body=True)
    assert cmd.succeeded
    # Verify route proxies to Pulp's Python plugin by checking for PythonDistribution in response
    # (Rails or unconfigured routes would return different errors)
    assert "PythonDistribution" in cmd.stdout


def test_pub_directory_exists(server):
    pub_dir = server.file(HTTPD_PUB_DIR)
    assert pub_dir.exists
    assert pub_dir.is_directory
    assert pub_dir.mode == 0o755


def test_http_pub_directory_accessible(curl_request):
    cmd = curl_request("pub/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pub_directory_accessible(curl_request):
    cmd = curl_request("pub/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_http_pub_server_ca_certificate_downloadable(curl_request):
    cmd = curl_request("pub/katello-server-ca.crt")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pub_server_ca_certificate_downloadable(curl_request):
    cmd = curl_request("pub/katello-server-ca.crt")
    assert cmd.succeeded
    assert cmd.stdout == '200'


@pytest.mark.feature('foreman')
def test_http_foreman_login(server, server_fqdn):
    cmd = server.run(f"{CURL_CMD} --write-out '%{{http_code}}' http://{server_fqdn}/users/login")
    assert cmd.succeeded
    assert cmd.stdout == '301'


@pytest.mark.feature('foreman')
def test_https_foreman_login(curl_request):
    cmd = curl_request("users/login")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_httpd_event_conf_exists(server):
    event_conf = server.file("/etc/httpd/conf.modules.d/event.conf")
    assert event_conf.exists
    assert event_conf.is_file


def test_httpd_event_conf_contains_server_limit(server):
    event_conf = server.file("/etc/httpd/conf.modules.d/event.conf")
    assert event_conf.contains("ServerLimit")


def test_httpd_event_conf_contains_threads_per_child(server):
    event_conf = server.file("/etc/httpd/conf.modules.d/event.conf")
    assert event_conf.contains("ThreadsPerChild")


def test_httpd_selinux_context(server):
    cmd = server.run("ls -1Z /etc/httpd/*.d/*.conf")
    assert cmd.succeeded
    incorrect = [line for line in cmd.stdout.splitlines() if line and ":httpd_config_t:" not in line]
    assert not incorrect, "Incorrect SELinux context (expected httpd_config_t):\n" + "\n".join(incorrect)


def test_httpd_config_syntax(server):
    cmd = server.run("httpd -t")
    assert cmd.succeeded


@pytest.mark.feature('foreman')
def test_httpd_headers_use_dashes(server):
    cmd = server.run("grep -rPn 'RequestHeader\\s+set\\s+\\S*_\\S*\\s' /etc/httpd/conf.d/foreman.conf /etc/httpd/conf.d/foreman-ssl.conf /etc/httpd/conf.d/05-foreman.d/ /etc/httpd/conf.d/05-foreman-ssl.d/ 2>/dev/null")
    assert cmd.stdout.strip() == '', f"HTTP header names should use dashes, not underscores:\n{cmd.stdout}"


@pytest.mark.feature('foreman')
def test_httpd_vhost_custom_logs_in_journal(server, server_fqdn, curl_request):
    http_marker = 'httpd-journal-http-access-test'
    ssl_marker = 'httpd-journal-ssl-access-test'

    server.run(f"{CURL_CMD} http://{server_fqdn}/{http_marker}")
    curl_request(ssl_marker)

    http_access = server.run("journalctl -t httpd-access --since '2 min ago' --no-pager").stdout
    ssl_access = server.run("journalctl -t httpd-ssl-access --since '2 min ago' --no-pager").stdout

    assert http_marker in http_access
    assert http_marker not in ssl_access
    assert ssl_marker in ssl_access
    assert ssl_marker not in http_access


@pytest.mark.feature('foreman')
def test_httpd_vhost_error_logs_in_journal(server):
    server.run(
        "printf 'GET /http-error-test HTTP/1.0\\r\\n\\r\\n' | nc -w 2 127.0.0.1 80 >/dev/null 2>&1 || true"
    )
    server.run(
        "(echo -e 'GET /ssl-error-test HTTP/1.0\\r\\n\\r\\n'; sleep 1) | "
        "openssl s_client -connect 127.0.0.1:443 -quiet >/dev/null 2>&1 || true"
    )

    http_error = server.run("journalctl -t httpd-error --since '2 min ago' --no-pager").stdout
    ssl_error = server.run("journalctl -t httpd-ssl-error --since '2 min ago' --no-pager").stdout

    assert 'http-error-test' in http_error
    assert 'http-error-test' not in ssl_error
    assert 'ssl-error-test' in ssl_error
    assert 'ssl-error-test' not in http_error


def test_httpd_foreman_target_config(server):
    drop_in = server.file("/etc/systemd/system/httpd.service.d/foreman-target.conf")
    assert drop_in.exists
    assert drop_in.is_file
    assert drop_in.contains("PartOf=foreman.target")
    assert drop_in.contains(r"WantedBy=default\.target foreman\.target")

    wants_link = server.file("/etc/systemd/system/foreman.target.wants/httpd.service")
    assert wants_link.exists
    assert wants_link.is_symlink
