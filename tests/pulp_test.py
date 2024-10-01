import json

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
    status = host.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' http://{PULP_HOST}:{PULP_PORT}/pulp/api/v3/status/")
    assert status.succeeded
    assert status.stderr == '200'

    status_json = json.loads(status.stdout)
    assert status_json['database_connection']['connected']
    assert status_json['redis_connection']['connected']
    assert status_json['online_api_apps']
    assert status_json['online_content_apps']
    assert status_json['online_workers']
