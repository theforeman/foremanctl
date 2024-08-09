def test_postgresql_service(host):
    postgresql = host.service("postgresql")
    assert postgresql.is_running
    assert postgresql.is_enabled


def test_postgresql_port(host):
    postgresql = host.addr("localhost")
    assert postgresql.port("5432").is_reachable
