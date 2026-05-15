VALKEY_HOST = 'localhost'
VALKEY_PORT = 6379


def test_valkey_service(server):
    valkey = server.service("valkey")
    assert valkey.is_running


def test_redis_service_absent(server):
    redis = server.service("redis")
    assert not redis.exists


def test_valkey_port(server):
    valkey = server.addr(VALKEY_HOST)
    assert valkey.port(VALKEY_PORT).is_reachable
