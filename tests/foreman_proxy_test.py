import json

import pytest


FOREMAN_PROXY_HOST = 'localhost'
FOREMAN_PROXY_PORT = 9090


@pytest.fixture(scope="module")
def foreman_proxy_version_curl(server):
    return server.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' https://{FOREMAN_PROXY_HOST}:{FOREMAN_PROXY_PORT}/version")


@pytest.fixture(scope="module")
def foreman_proxy_features_curl(server):
    return server.run(f"curl -k -s -w '%{{stderr}}%{{http_code}}' --cert /root/certificates/certs/quadlet.example.com-client.crt --key /root/certificates/private/quadlet.example.com-client.key https://{FOREMAN_PROXY_HOST}:{FOREMAN_PROXY_PORT}/v2/features")


def test_foreman_proxy_service(server):
    foreman_proxy = server.service("foreman-proxy")
    assert foreman_proxy.is_running
    assert foreman_proxy.is_enabled


def test_foreman_proxy_port(server):
    foreman_proxy = server.addr(FOREMAN_PROXY_HOST)
    assert foreman_proxy.port(FOREMAN_PROXY_PORT).is_reachable


def test_foreman_proxy_version(foreman_proxy_version_curl):
    assert foreman_proxy_version_curl.succeeded
    assert foreman_proxy_version_curl.stderr == '200'


def test_foreman_proxy_features(foreman_proxy_features_curl):
    assert foreman_proxy_features_curl.succeeded
    assert foreman_proxy_features_curl.stderr == '200'


def test_pulpcore_feature(foreman_proxy_features_curl):
    features = json.loads(foreman_proxy_features_curl.stdout)
    assert 'pulpcore' in features.keys()
