import json
import pytest
from conftest import GenericService, get_service

PULP_HOST = 'localhost'
PULP_API_PORT = 24817
PULP_CONTENT_PORT = 24816

@pytest.fixture(scope="module")
def pulp_status_curl(server):
    return server.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' http://{PULP_HOST}:{PULP_API_PORT}/pulp/api/v3/status/")

@pytest.fixture(scope="module")
def pulp_status(pulp_status_curl):
    return json.loads(pulp_status_curl.stdout)

def test_pulp_api_service(server, user):
    pulp_api = get_service(server, "pulp-api", user)
    assert pulp_api.is_running


def test_pulp_content_service(server, user):
    pulp_content = get_service(server, "pulp-content", user)
    assert pulp_content.is_running

def test_pulp_worker_services(server, user):
    if user:
        result = server.run(f"systemctl --machine={user}@ --user list-units --all --type=service --no-legend 'pulp-worker@*.service' | awk '{{print $1}}'")
    else:
        result = server.run("systemctl list-units --all --type=service --no-legend 'pulp-worker@*.service' | awk '{print $1}'")
    worker_services = [s.strip() for s in result.stdout.split('\n') if s.strip()]
    assert len(worker_services) > 0

    for worker_service in worker_services:
        worker = get_service(server, worker_service, user)
        assert worker.is_running

def test_pulp_api_port(server):
    pulp_api = server.addr(PULP_HOST)
    assert pulp_api.port(PULP_API_PORT).is_reachable

def test_pulp_content_port(server):
    pulp_content = server.addr(PULP_HOST)
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


def test_pulp_volumes(server):
    assert server.file("/var/lib/pulp").is_directory

def test_pulp_worker_target(server, user):
    pulp_worker_target = get_service(server, "pulp-worker.target", user)
    assert pulp_worker_target.is_running
    assert pulp_worker_target.is_enabled


def test_pulp_manager_check(server, user):
    if user:
        result = server.run(f"cd /tmp && sudo -u {user} podman exec -ti pulp-api pulpcore-manager check --deploy")
    else:
        result = server.run("podman exec -ti pulp-api pulpcore-manager check --deploy")
    assert result.succeeded
