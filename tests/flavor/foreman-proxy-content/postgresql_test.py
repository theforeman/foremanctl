
def test_postgresql_databases(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\l'")
    assert "pulp" in result.stdout
    assert "foreman" not in result.stdout
    assert "candlepin" not in result.stdout


def test_postgresql_users(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\du'")
    assert "pulp" in result.stdout
    assert "foreman" not in result.stdout
    assert "candlepin" not in result.stdout
