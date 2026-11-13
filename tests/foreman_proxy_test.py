
import datetime
import json
import shlex
from urllib.parse import urlencode

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
    """Make authenticated requests to the Foreman Proxy API."""

    def _request(path, method="GET", data=None):
        url = f"https://{server_fqdn}:{FOREMAN_PROXY_PORT}/{path}"

        curl_opts = (
            "curl --silent --show-error --fail-with-body "
            "--write-out '\\n%{http_code}' "
            f"--cacert {shlex.quote(certificates['server_ca_certificate'])} "
            f"--cert {shlex.quote(certificates['client_certificate'])} "
            f"--key {shlex.quote(certificates['client_key'])} "
            f"--request {shlex.quote(method)} "
        )

        if data is not None:
            curl_opts += (
                "-H 'Content-Type: application/x-www-form-urlencoded' "
                f"--data {shlex.quote(urlencode(data))} "
            )

        cmd = server.run(f"{curl_opts}{shlex.quote(url)}")

        assert cmd.succeeded, (
            f"{method} {path} failed: "
            f"{cmd.stdout}\n{cmd.stderr}"
        )

        body, status = cmd.stdout.rsplit("\n", 1)
        return int(status), body

    return _request


def test_foreman_proxy_features(
    server, certificates, server_fqdn, enabled_features
):
    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features"
    )
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
def test_foreman_proxy_client_auth_to_foreman(
    server, certificates, server_fqdn
):
    test_report = {
        "config_report": {
            "host": "test.example.com",
            "reported_at": datetime.datetime.now(
                datetime.UTC
            ).strftime('%Y-%m-%d %H:%M:%S UTC')
        }
    }

    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--output /dev/null --write-out '%{{http_code}}' "
        f"--data '{json.dumps(test_report)}' "
        f"--header 'Content-Type: application/json' "
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
    """Verify the DHCP feature is registered."""
    assert 'dhcp' in proxy_v2_features


@pytest.mark.feature('dhcp')
def test_dhcp_provider(proxy_v2_features):
    """Verify DHCP uses the Kea provider."""
    settings = proxy_v2_features['dhcp'].get('settings', {})
    assert settings.get('use_provider') == 'dhcp_kea'


@pytest.mark.feature('dhcp')
def test_dhcp_kea_capabilities(proxy_v2_features):
    """Verify Kea DHCP provider capabilities."""
    capabilities = proxy_v2_features['dhcp'].get('capabilities', [])

    assert 'dhcp_filename_ipv4' in capabilities
    assert 'dhcp_filename_hostname' in capabilities


@pytest.mark.feature('dhcp')
def test_dhcp_kea_list_subnets(proxy_request):
    """Verify subnet discovery through the Smart Proxy DHCP API."""
    status, body = proxy_request("dhcp")

    assert status == 200

    subnets = json.loads(body)
    assert isinstance(subnets, list), "Expected a list of subnets"

    assert any(
        subnet["network"] == "192.168.122.0"
        and subnet["netmask"] == "255.255.255.0"
        for subnet in subnets
    ), f"Expected Kea test subnet not found: {subnets}"


@pytest.mark.feature('dhcp')
def test_dhcp_kea_create_and_delete_reservation(proxy_request):
    """Verify reservation CRUD through the Smart Proxy DHCP API."""
    network = "192.168.122.0"
    test_ip = "192.168.122.210"
    test_mac = "02:00:00:00:de:02"
    test_hostname = "foremanctl-test-host"

    reservation_data = {
        "ip": test_ip,
        "mac": test_mac,
        "hostname": test_hostname,
    }

    status, body = proxy_request(
        f"dhcp/{network}",
        method="POST",
        data=reservation_data,
    )

    assert status in (200, 201), (
        f"Failed to create reservation: {body}"
    )

    try:
        status, body = proxy_request(
            f"dhcp/{network}/ip/{test_ip}"
        )

        assert status == 200

        records = json.loads(body)
        assert isinstance(records, list)
        assert len(records) == 1

        reservation = records[0]

        assert reservation["ip"] == test_ip
        assert reservation["mac"] == test_mac
        assert reservation["name"] == test_hostname

    finally:
        status, body = proxy_request(
            f"dhcp/{network}/ip/{test_ip}",
            method="DELETE",
        )

        assert status in (200, 204), (
            f"Failed to delete reservation: {body}"
        )

    status, body = proxy_request(f"dhcp/{network}")

    assert status == 200

    records = json.loads(body)["reservations"]

    assert not any(
        record["ip"] == test_ip for record in records
    ), f"Reservation still exists for {test_ip}"
