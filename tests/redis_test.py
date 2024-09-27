import pytest


REDIS_HOST = 'localhost'
REDIS_PORT = 6379


def test_redis_service(host):
    redis = host.service("redis")
    assert redis.is_running
    assert redis.is_enabled


def test_redis_port(host):
    redis = host.addr(REDIS_HOST)
    assert redis.port(REDIS_PORT).is_reachable
