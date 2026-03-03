import pytest
from conftest import get_service


REDIS_HOST = 'localhost'
REDIS_PORT = 6379


def test_redis_service(server, user):
    redis = get_service(server, "redis", user)
    assert redis.is_running


def test_redis_port(server):
    redis = server.addr(REDIS_HOST)
    assert redis.port(REDIS_PORT).is_reachable
