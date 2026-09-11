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
    assert not valkey.port(VALKEY_PORT).is_reachable


def test_valkey_not_listening_on_all_interfaces(server):

    ports = server.run("podman port valkey")
    assert f'127.0.0.1:{VALKEY_PORT}' not in ports.stdout
    assert f'0.0.0.0:{VALKEY_PORT}' not in ports.stdout

    ss = server.run(f"ss -ltn '( sport = :{VALKEY_PORT} )'")
    assert f'0.0.0.0:{VALKEY_PORT}' not in ss.stdout
    assert f'[::]:{VALKEY_PORT}' not in ss.stdout
