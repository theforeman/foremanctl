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


@pytest.fixture(scope="module")
def proxy_request(server, certificates, server_fqdn):
    """Helper fixture for making authenticated requests to Foreman Proxy API"""
    def _request(path, method=None, data=None, return_body=False):
        curl_opts = (
            f"--cacert {certificates['server_ca_certificate']} "
            f"--cert {certificates['client_certificate']} "
            f"--key {certificates['client_key']} "
            f"--silent "
        )
        if not return_body:
            curl_opts += "--output /dev/null --write-out '%{http_code}' "
        if method:
            curl_opts += f"-X {method} "
        if data:
            curl_opts += f"-H 'Content-Type: application/json' -d '{data}' "
        return server.run(f"curl {curl_opts}https://{server_fqdn}:{FOREMAN_PROXY_PORT}/{path}")

    return _request


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
    if 'dhcp' in enabled_features:
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


@pytest.mark.feature('dhcp')
def test_dhcp_feature_present(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features


@pytest.mark.feature('dhcp')
def test_dhcp_provider(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features
    settings = proxy_v2_features['dhcp'].get('settings', {})
    assert settings.get('use_provider') == 'dhcp_kea'


@pytest.mark.feature('dhcp')
def test_dhcp_kea_api_settings(proxy_v2_features):
    assert 'dhcp' in proxy_v2_features
    settings = proxy_v2_features['dhcp'].get('settings', {})
    assert 'kea_api_url' in settings
    assert settings['kea_api_url'].endswith(':8000')
    if settings.get('managed_subnets'):
        assert isinstance(settings['managed_subnets'], list)
        assert all('/' in subnet for subnet in settings['managed_subnets'])


@pytest.mark.feature('dhcp')
def test_dhcp_kea_list_subnets(proxy_request):
    """Test listing subnets from Kea via Foreman Proxy DHCP API"""
    cmd = proxy_request("dhcp", return_body=True)
    assert cmd.succeeded, f"Failed to list DHCP subnets: {cmd.stderr}"

    subnets = json.loads(cmd.stdout)
    assert isinstance(subnets, list), "Expected subnet list"

    subnet_networks = [s['network'] for s in subnets]
    assert '192.168.122.0/24' in subnet_networks, f"Test subnet not found in {subnet_networks}"


@pytest.mark.feature('dhcp')
def test_dhcp_kea_create_and_delete_reservation(proxy_request):
    """Test creating and deleting a DHCP reservation via Kea"""
    test_mac = "aa:bb:cc:dd:ee:ff"
    test_ip = "192.168.122.150"
    test_hostname = "foremanctl-test-host"

    reservation_data = json.dumps({
        "network": "192.168.122.0/24",
        "ip": test_ip,
        "mac": test_mac,
        "hostname": test_hostname,
        "subnet": "192.168.122.0",
        "netmask": "255.255.255.0"
    })

    cmd = proxy_request(
        f"dhcp/192.168.122.0/255.255.255.0/{test_ip}",
        method="POST",
        data=reservation_data
    )
    assert cmd.succeeded, f"Failed to create DHCP reservation: {cmd.stderr}"
    assert cmd.stdout == '200', f"Expected HTTP 200 when creating reservation, got {cmd.stdout}"

    cmd = proxy_request(f"dhcp/192.168.122.0/255.255.255.0/{test_ip}", return_body=True)
    assert cmd.succeeded, f"Failed to query DHCP reservation: {cmd.stderr}"

    reservation = json.loads(cmd.stdout)
    assert reservation['ip'] == test_ip
    assert reservation['mac'] == test_mac
    assert reservation['hostname'] == test_hostname

    cmd = proxy_request(
        f"dhcp/192.168.122.0/255.255.255.0/{test_ip}",
        method="DELETE"
    )
    assert cmd.succeeded, f"Failed to delete DHCP reservation: {cmd.stderr}"
    assert cmd.stdout == '200', f"Expected HTTP 200 when deleting reservation, got {cmd.stdout}"
