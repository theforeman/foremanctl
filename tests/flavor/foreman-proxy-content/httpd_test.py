CURL_CMD = "curl --silent --output /dev/null"


def test_pulpcore_vhost_exists(server):
    conf = server.file("/etc/httpd/conf.d/pulpcore.conf")
    assert conf.exists
    assert conf.is_file


def test_https_pulp_api_with_client_cert(curl_request):
    cmd = curl_request("pulp/api/v3/smart_proxy/v2/features")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_rhsm_proxy(curl_request):
    cmd = curl_request("rhsm")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_redhat_access_proxy(curl_request):
    cmd = curl_request("redhat_access")
    assert cmd.succeeded
    assert cmd.stdout not in ('502', '503')


def test_rhsm_proxy_timeout(server):
    vhost = server.file("/etc/httpd/conf.d/pulpcore-ssl.conf")
    assert vhost.contains(r"ProxyPass /rhsm .* timeout=180")


def test_redhat_access_proxy_timeout(server):
    vhost = server.file("/etc/httpd/conf.d/pulpcore-ssl.conf")
    assert vhost.contains(r"ProxyPass /redhat_access .* timeout=120")


def test_https_pulp_content_proxy(curl_request):
    cmd = curl_request("pulp/content/")
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulpcore_registry(curl_request):
    cmd = curl_request("pulpcore_registry/v2/")
    assert cmd.succeeded
    assert cmd.stdout not in ('404', '502', '503')
