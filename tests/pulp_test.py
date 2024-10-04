import json

import pytest


PULP_HOST = 'localhost'
PULP_PORT = 8080


@pytest.fixture(scope="module")
def pulp_status_curl(host):
    return host.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' http://{PULP_HOST}:{PULP_PORT}/pulp/api/v3/status/")


@pytest.fixture(scope="module")
def pulp_status(pulp_status_curl):
    return json.loads(pulp_status_curl.stdout)


def test_pulp_service(host):
    pulp = host.service("pulp")
    assert pulp.is_running
    assert pulp.is_enabled


def test_pulp_port(host):
    pulp = host.addr(PULP_HOST)
    assert pulp.port(PULP_PORT).is_reachable


def test_pulp_status(pulp_status_curl):
    assert pulp_status_curl.succeeded
    assert pulp_status_curl.stderr == '200'


def test_pulp_status_database_connection(pulp_status):
    assert pulp_status['database_connection']['connected']


def test_pulp_status_redis_connection(pulp_status):
    assert pulp_status['redis_connection']['connected']


def test_pulp_status_api(pulp_status):
    assert pulp_status['online_api_apps']


def test_pulp_status_content(pulp_status):
    assert pulp_status['online_content_apps']


def test_pulp_status_workers(pulp_status):
    assert pulp_status['online_workers']
