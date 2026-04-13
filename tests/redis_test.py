def test_redis_service(server):
    redis = server.service("redis")
    assert redis.is_running


def test_redis_ping(server):
    result = server.run("podman exec redis redis-cli ping")
    assert result.succeeded
    assert result.stdout.strip() == "PONG"
