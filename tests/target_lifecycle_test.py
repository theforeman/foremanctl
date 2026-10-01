import time

import pytest

TARGET_ACTIVE_RETRIES = 90
TARGET_ACTIVE_DELAY = 10
SOCKET_INACTIVE_RETRIES = 90
SOCKET_INACTIVE_DELAY = 1
CURL_CMD = "curl --silent --output /dev/null"
SOCKET_UNITS = ("foreman.socket", "pulp-api.socket", "pulp-content.socket")

pytestmark = pytest.mark.slow


def _wait_for_target_active(server, target="foreman.target"):
    for _ in range(TARGET_ACTIVE_RETRIES):
        if server.service(target).is_running:
            return
        time.sleep(TARGET_ACTIVE_DELAY)
    raise AssertionError(f"{target} did not become active after lifecycle operation")


def _loaded_socket_units(server):
    return [
        unit
        for unit in SOCKET_UNITS
        if server.run(f"systemctl show --property=LoadState --value {unit}").stdout.strip() == "loaded"
    ]


def _wait_for_sockets_inactive(server, socket_units):
    for _ in range(SOCKET_INACTIVE_RETRIES):
        if all(not server.service(unit).is_running for unit in socket_units):
            return
        time.sleep(SOCKET_INACTIVE_DELAY)
    raise AssertionError(f"Socket units did not stop: {', '.join(socket_units)}")


def test_foreman_target_stop_start(server, server_fqdn, certificates):
    socket_units = _loaded_socket_units(server)
    assert socket_units

    for unit in socket_units:
        assert "foreman.target" in server.service(unit).systemd_properties.get("PartOf")

    result = server.run("systemctl stop foreman.target")
    assert result.rc == 0, f"Failed to stop foreman.target: {result.stderr}"
    assert not server.service("foreman.target").is_running
    _wait_for_sockets_inactive(server, socket_units)
    for unit in socket_units:
        assert not server.service(unit).is_running

    result = server.run("systemctl start foreman.target")
    assert result.rc == 0, f"Failed to start foreman.target: {result.stderr}"
    _wait_for_target_active(server, "foreman.target")
    assert server.service("foreman.target").is_running
    for unit in socket_units:
        assert server.service(unit).is_running


def test_foreman_target_restart(server, server_fqdn, certificates):
    result = server.run("systemctl restart foreman.target")
    assert result.rc == 0, f"Failed to restart foreman.target: {result.stderr}"
    _wait_for_target_active(server, "foreman.target")
    assert server.service("foreman.target").is_running
