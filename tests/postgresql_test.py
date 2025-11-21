import csv

def test_postgresql_service(server):
    postgresql = server.service("postgresql")
    assert postgresql.is_running

def test_postgresql_port(server):
    postgresql = server.addr("localhost")
    assert postgresql.port("5432").is_reachable


def test_postgresql_databases(server):
    result = server.run("podman exec postgresql psql -U postgres -c '\\l'")
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
    assert "pulp" in result.stdout


def test_postgresql_users(server):
    result = server.run("podman exec postgresql psql -U postgres -c '\\du'")
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
    assert "pulp" in result.stdout

def test_postgresql_password_encryption(server):
    result = server.run("podman exec postgresql psql -U postgres -c 'SHOW password_encryption'")
    assert "scram-sha-256" in result.stdout

    result = server.run("echo 'COPY (select * from pg_shadow) TO STDOUT (FORMAT CSV);' | podman exec -i postgresql psql -U postgres")

    reader = csv.reader(result.stdout.splitlines())
    for row in reader:
        assert ("SCRAM-SHA-256" in row[6])
