import pytest


def test_valkey_service(server):
    valkey = server.service("valkey")
    assert valkey.is_running


def test_redis_service_absent(server):
    redis = server.service("redis")
    assert not redis.exists


def test_valkey_not_exposed_on_host(server):
    valkey = server.addr("localhost")
    assert not valkey.port("6379").is_reachable


@pytest.mark.feature('foreman')
def test_valkey_resolves_from_foreman(server):
    result = server.run("podman exec foreman getent hosts valkey")
    assert result.succeeded


def test_valkey_ping(server):
    result = server.run("podman exec valkey valkey-cli ping")
    assert result.succeeded
    assert result.stdout.strip() == "PONG"
