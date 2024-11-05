import json
import pytest


PULP_HOST = 'localhost'
PULP_API_PORT = 24817
PULP_CONTENT_PORT = 24816

@pytest.fixture(scope="module")
def pulp_status_curl(host):
    return host.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' http://{PULP_HOST}:{PULP_API_PORT}/pulp/api/v3/status/")


@pytest.fixture(scope="module")
def pulp_status(pulp_status_curl):
    return json.loads(pulp_status_curl.stdout)


def test_pulp_service(host):
    pulp = host.service("pulp")
    assert pulp.is_running
    assert pulp.is_enabled

def test_pulp_api_service(host):
    pulp_api = host.service("pulp-api")
    assert pulp_api.is_running
    assert pulp_api.is_enabled

def test_pulp_content_service(host):
    pulp_content = host.service("pulp-content")
    assert pulp_content.is_running
    assert pulp_content.is_enabled

def test_pulp_worker_services(host):
    for i in range(1, 3):
        pulp_worker = host.service(f"pulp-worker@{i}")
        assert pulp_worker.is_running
        assert pulp_worker.is_enabled

def test_pulp_api_port(host):
    pulp_api = host.addr(PULP_HOST)
    assert pulp_api.port(PULP_API_PORT).is_reachable

def test_pulp_content_port(host):
    pulp_content = host.addr(PULP_HOST)
    assert pulp_content.port(PULP_CONTENT_PORT).is_reachable

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

@pytest.mark.xfail(reason='password auth is deactivated when we use cert auth')
def test_pulp_admin_auth(host):
    cmd = host.run(f"curl --silent --write-out '%{{stderr}}%{{http_code}}' --user admin:CHANGEME http://{PULP_HOST}:{PULP_API_PORT}/pulp/api/v3/users/")
    assert cmd.succeeded
    assert cmd.stderr == '200'
