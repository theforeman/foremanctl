import pytest


REDIS_HOST = 'localhost'
REDIS_PORT = 6379


def test_redis_service(server):
    redis = server.service("redis")
    assert redis.is_running


def test_redis_port(server):
    redis = server.addr(REDIS_HOST)
    assert redis.port(REDIS_PORT).is_reachable
