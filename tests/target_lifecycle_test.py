import time
import pytest

FOREMAN_PING_RETRIES = 60
FOREMAN_PING_DELAY = 10
CURL_CMD = "curl --silent --output /dev/null"


def _wait_for_foreman(server, server_fqdn, certificates, database_mode=None):
    """Poll the Foreman HTTPS frontend until available or timeout."""
    retries = FOREMAN_PING_RETRIES
    if database_mode == 'external':
        retries = 90  # External DB with SSL needs more time to reconnect
    for _ in range(retries):
        cmd = server.run(
            f"{CURL_CMD} --cacert {certificates['ca_certificate']}"
            f" --write-out '%{{http_code}}' https://{server_fqdn}/api/v2/ping"
        )
        if cmd.stdout == '200':
            return
        time.sleep(FOREMAN_PING_DELAY)
    raise AssertionError("Foreman did not become available after target lifecycle operation")


def _systemctl(server, user, action, target):
    """Run a systemctl command, using user scope if rootless."""
    if user:
        return server.run(f"systemctl --machine={user}@ --user {action} {target}")
    return server.run(f"systemctl {action} {target}")


def test_foreman_target_stop_start(server, server_fqdn, certificates, user, database_mode):
    result = _systemctl(server, user, "stop", "foreman.target")
    assert result.rc == 0, f"Failed to stop foreman.target: {result.stderr}"

    result = _systemctl(server, user, "start", "foreman.target")
    assert result.rc == 0, f"Failed to start foreman.target: {result.stderr}"
    _wait_for_foreman(server, server_fqdn, certificates, database_mode)


def test_foreman_target_restart(server, server_fqdn, certificates, user, database_mode):
    result = _systemctl(server, user, "restart", "foreman.target")
    assert result.rc == 0, f"Failed to restart foreman.target: {result.stderr}"
    _wait_for_foreman(server, server_fqdn, certificates, database_mode)
