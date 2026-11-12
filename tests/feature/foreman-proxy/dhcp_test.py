
"""Integration tests for the Smart Proxy DHCP feature."""

import json
from urllib.parse import urlencode

import pytest


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
def test_dhcp_kea_list_subnets(curl_request, proxy_base_url):
    """Verify subnet discovery through the Smart Proxy DHCP API."""
    response = curl_request(
        "dhcp",
        base_url=proxy_base_url,
        return_body=True,
    )

    assert response.succeeded, response.stderr

    subnets = json.loads(response.stdout)
    assert isinstance(subnets, list), "Expected a list of subnets"

    assert any(
        subnet["network"] == "192.168.122.0"
        and subnet["netmask"] == "255.255.255.0"
        for subnet in subnets
    ), f"Expected Kea test subnet not found: {subnets}"


@pytest.mark.feature('dhcp')
def test_dhcp_kea_create_and_delete_reservation(
    curl_request, proxy_base_url
):
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

    response = curl_request(
        f"dhcp/{network}",
        base_url=proxy_base_url,
        method="POST",
        data=urlencode(reservation_data),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.succeeded, response.stderr
    assert response.stdout.strip() in ("200", "201")

    try:
        response = curl_request(
            f"dhcp/{network}/ip/{test_ip}",
            base_url=proxy_base_url,
            return_body=True,
        )

        assert response.succeeded, response.stderr

        records = json.loads(response.stdout)
        assert isinstance(records, list)
        assert len(records) == 1

        reservation = records[0]

        assert reservation["ip"] == test_ip
        assert reservation["mac"] == test_mac
        assert reservation["name"] == test_hostname

    finally:
        response = curl_request(
            f"dhcp/{network}/ip/{test_ip}",
            base_url=proxy_base_url,
            method="DELETE",
        )

        assert response.succeeded, response.stderr
        assert response.stdout.strip() in ("200", "204")

    response = curl_request(
        f"dhcp/{network}",
        base_url=proxy_base_url,
        return_body=True,
    )

    assert response.succeeded, response.stderr

    records = json.loads(response.stdout)["reservations"]

    assert not any(
        record["ip"] == test_ip for record in records
    ), f"Reservation still exists for {test_ip}"
