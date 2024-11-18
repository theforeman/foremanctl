def test_postgresql_service(server):
    postgresql = server.service("postgresql")
    assert postgresql.is_running
    assert postgresql.is_enabled


def test_postgresql_port(server):
    postgresql = server.addr("localhost")
    assert postgresql.port("5432").is_reachable
