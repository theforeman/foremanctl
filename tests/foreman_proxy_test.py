import datetime
import json

import pytest

FOREMAN_PROXY_PORT = 8443


@pytest.fixture(scope="module")
def proxy_v2_features(server, certificates, server_fqdn):
    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/v2/features"
    )
    assert cmd.succeeded, f"Failed to query /v2/features: {cmd.stderr}"
    return json.loads(cmd.stdout)


def test_foreman_proxy_features(server, certificates, server_fqdn, enabled_features):
    cmd = server.run(f"curl --cacert {certificates['server_ca_certificate']} --silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features")
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "logs" in features
    assert "script" in features
    assert "dynflow" in features
    if 'bmc' in enabled_features:
        assert "bmc" in features
    else:
        assert "bmc" not in features
    if 'dhcp-kea-external' in enabled_features:
        assert "dhcp" in features
    else:
        assert "dhcp" not in features


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


@pytest.mark.feature('dhcp-kea-external')
def test_dhcp_kea_feature_present(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features


@pytest.mark.feature('dhcp-kea-external')
def test_dhcp_kea_provider(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features
    settings = proxy_v2_features['dhcp'].get('settings', {})
    assert settings.get('use_provider') == 'dhcp_kea_api'


@pytest.mark.feature('dhcp-kea-external')
def test_dhcp_kea_server_settings(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features
    settings = proxy_v2_features['dhcp'].get('settings', {})
    assert 'server' in settings
    assert 'kea_url' in settings
    assert settings['kea_url'].endswith(':8000')
    assert 'kea_subnet' in settings
    assert '/' in settings['kea_subnet']
