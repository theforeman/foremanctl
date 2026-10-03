import time

import pytest

pytestmark = pytest.mark.slow

TARGET_ACTIVE_RETRIES = 90
TARGET_ACTIVE_DELAY = 10
CURL_CMD = "curl --silent --output /dev/null"


def _wait_for_target_active(server, target="foreman.target"):
    for _ in range(TARGET_ACTIVE_RETRIES):
        if server.service(target).is_running:
            return
        time.sleep(TARGET_ACTIVE_DELAY)
    raise AssertionError(f"{target} did not become active after lifecycle operation")


def test_foreman_target_stop_start(server, server_fqdn, certificates):
    result = server.run("systemctl stop foreman.target")
    assert result.rc == 0, f"Failed to stop foreman.target: {result.stderr}"
    assert not server.service("foreman.target").is_running

    result = server.run("systemctl start foreman.target")
    assert result.rc == 0, f"Failed to start foreman.target: {result.stderr}"
    _wait_for_target_active(server, "foreman.target")
    assert server.service("foreman.target").is_running


def test_foreman_target_restart(server, server_fqdn, certificates):
    result = server.run("systemctl restart foreman.target")
    assert result.rc == 0, f"Failed to restart foreman.target: {result.stderr}"
    _wait_for_target_active(server, "foreman.target")
    assert server.service("foreman.target").is_running
