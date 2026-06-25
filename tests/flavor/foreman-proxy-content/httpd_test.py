CURL_CMD = "curl --silent --output /dev/null"


def test_pulpcore_vhost_exists(server):
    conf = server.file("/etc/httpd/conf.d/pulpcore.conf")
    assert conf.exists
    assert conf.is_file


def test_https_pulp_api_with_client_cert(server, certificates, server_fqdn):
    cmd = server.run(
        f"curl --silent --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--write-out '%{{http_code}}' --output /dev/null "
        f"https://{server_fqdn}/pulp/api/v3/smart_proxy/v2/features"
    )
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_rhsm_proxy(server, certificates, server_fqdn):
    cmd = server.run(
        f"{CURL_CMD} --cacert {certificates['server_ca_certificate']} "
        f"--write-out '%{{http_code}}' "
        f"https://{server_fqdn}/rhsm"
    )
    assert cmd.succeeded
    assert cmd.stdout not in ('404', '502', '503')


def test_https_pulp_content_proxy(server, certificates, server_fqdn):
    cmd = server.run(
        f"{CURL_CMD} --cacert {certificates['server_ca_certificate']} "
        f"--write-out '%{{http_code}}' "
        f"https://{server_fqdn}/pulp/content/"
    )
    assert cmd.succeeded
    assert cmd.stdout == '200'


def test_https_pulpcore_registry(server, certificates, server_fqdn):
    cmd = server.run(
        f"{CURL_CMD} --cacert {certificates['server_ca_certificate']} "
        f"--write-out '%{{http_code}}' "
        f"https://{server_fqdn}/pulpcore_registry/v2/"
    )
    assert cmd.succeeded
    assert cmd.stdout not in ('404', '502', '503')
