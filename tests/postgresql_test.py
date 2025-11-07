import csv
import pytest


def test_postgresql_service(database):
    postgresql = database.service("postgresql")
    assert postgresql.is_running


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


def test_postgresql_password_encryption(database):
    result = database.run("podman exec postgresql psql -U postgres -c 'SHOW password_encryption'")
    assert "scram-sha-256" in result.stdout

    result = database.run("echo 'COPY (select * from pg_shadow) TO STDOUT (FORMAT CSV);' | podman exec -i postgresql psql -U postgres")

    reader = csv.reader(result.stdout.splitlines())
    for row in reader:
        assert ("SCRAM-SHA-256" in row[6])


def test_postgresql_missing_with_external(server, database_mode):
    if database_mode == 'internal':
        pytest.skip("Test only applies if database_mode=external")
    else:
        assert not server.service("postgresql").exists
