import datetime
import json

import pytest

from tests.conftest import FOREMAN_PROXY_PORT


@pytest.fixture(scope="module")
def proxy_v2_features(proxy_request):
    cmd = proxy_request("v2/features", return_body=True)
    assert cmd.succeeded, f"Failed to query /v2/features: {cmd.stderr}"
    return json.loads(cmd.stdout)


def test_foreman_proxy_features(proxy_request, enabled_features):
    cmd = proxy_request("features", return_body=True)
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "logs" in features
    assert "script" in features
    assert "dynflow" in features
    if 'bmc' in enabled_features:
        assert "bmc" in features
    else:
        assert "bmc" not in features
    if 'tftp' in enabled_features:
        assert "tftp" in features
    else:
        assert "tftp" not in features


def test_foreman_proxy_service(server):
    foreman_proxy = server.service("foreman-proxy")
    assert foreman_proxy.is_running


def test_foreman_proxy_port(server):
    foreman_proxy = server.addr('localhost')
    assert foreman_proxy.port(FOREMAN_PROXY_PORT).is_reachable


@pytest.mark.xfail(reason='Fails until report feature is available')
def test_foreman_proxy_client_auth_to_foreman(server, certificates, server_fqdn):
    test_report = {"config_report": {"host": "test.example.com", "reported_at": datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}}
    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--output /dev/null --write-out '%{{http_code}}' "
        f"--data '{json.dumps(test_report)}' --header 'Content-Type: application/json' "
        f"https://{server_fqdn}/api/v2/config_reports"
    )
    assert cmd.succeeded
    assert cmd.stdout == '201'


@pytest.mark.feature('tftp')
def test_tftp_write_and_fetch(proxy_request, server):
    test_mac = "aa:bb:cc:dd:ee:ff"
    cmd = proxy_request(f"tftp/{test_mac}", data="syslinux_config=foremanctl+test+probe")
    assert cmd.succeeded
    assert cmd.stdout == '200', f"Expected HTTP 200 when creating TFTP PXE config, got {cmd.stdout}"

    cmd = server.run("tftp 127.0.0.1 -c get pxelinux.cfg/01-aa-bb-cc-dd-ee-ff /tmp/foremanctl_tftp_test_download")
    assert cmd.succeeded, f"TFTP get failed: {cmd.stdout}"
    assert server.file("/tmp/foremanctl_tftp_test_download").content_string == "foremanctl test probe"


@pytest.mark.feature('bmc')
def test_bmc_capabilities(proxy_v2_features):
    assert 'bmc' in proxy_v2_features
    capabilities = proxy_v2_features['bmc'].get('capabilities', [])
    assert 'ipmitool' in capabilities
    assert 'freeipmi' in capabilities
    assert 'redfish' in capabilities


@pytest.mark.feature('bmc')
def test_bmc_default_provider(proxy_v2_features):
    settings = proxy_v2_features['bmc'].get('settings', {})
    assert settings.get('bmc_default_provider') == 'ipmitool'
