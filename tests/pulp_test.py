import pytest


PULP_HOST = 'localhost'
PULP_PORT = 8080


def test_pulp_service(host):
    pulp = host.service("pulp")
    assert pulp.is_running
    assert pulp.is_enabled


def test_pulp_port(host):
    pulp = host.addr(PULP_HOST)
    assert pulp.port(PULP_PORT).is_reachable


def test_pulp_status(host):
    status = host.run(f"curl -k -s -o /dev/null -w '%{{http_code}}' http://{PULP_HOST}:{PULP_PORT}/pulp/api/v3/status/")
    assert status.succeeded
    assert status.stdout == '200'
