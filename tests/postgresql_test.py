import pytest


def test_postgresql_service(database):
    postgresql = database.service("postgresql")
    assert postgresql.is_running
    assert postgresql.is_enabled


def test_postgresql_port(database):
    postgresql = database.addr("localhost")
    assert postgresql.port("5432").is_reachable


def test_postgresql_databases(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\l'")
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
    assert "pulp" in result.stdout


def test_postgresql_users(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\du'")
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
    assert "pulp" in result.stdout


def test_postgresql_missing_with_external(server, database_mode):
    if database_mode == 'internal':
        pytest.skip("Test only applies if database_mode=external")
    else:
        assert not server.service("postgresql").exists
