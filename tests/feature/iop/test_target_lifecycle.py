import time

import pytest

TARGET_ACTIVE_RETRIES = 90
TARGET_ACTIVE_DELAY = 10

pytestmark = pytest.mark.slow


def _wait_for_target_active(server, target="foreman.target"):
    for _ in range(TARGET_ACTIVE_RETRIES):
        if server.service(target).is_running:
            return
        time.sleep(TARGET_ACTIVE_DELAY)
    raise AssertionError(f"{target} did not become active after lifecycle operation")


def _wait_for_no_iop_containers(server, retries=30, delay=2):
    for _ in range(retries):
        result = server.run("podman ps --filter name=iop --format '{{.Names}}'")
        if not result.stdout.strip():
            return
        time.sleep(delay)
    raise AssertionError(f"IOP containers still running after stop: {result.stdout}")


def test_foreman_target_stop_starts_iop_services(server):
    result = server.run("systemctl stop foreman.target")
    assert result.rc == 0, f"Failed to stop foreman.target: {result.stderr}"
    assert not server.service("foreman.target").is_running

    _wait_for_no_iop_containers(server)

    result = server.run("systemctl start foreman.target")
    assert result.rc == 0, f"Failed to start foreman.target: {result.stderr}"
    _wait_for_target_active(server)
    assert server.service("foreman.target").is_running

    result = server.run("podman ps --filter name=iop --filter status=running --format '{{.Names}}'")
    assert result.stdout.strip(), "No IOP containers running after start"
