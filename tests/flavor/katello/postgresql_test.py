
def test_postgresql_databases(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\l'")
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
    assert "pulp" in result.stdout


def test_postgresql_users(database):
    result = database.run("podman exec postgresql psql -U postgres -c '\\du'")
    assert "pulp" in result.stdout
    assert "foreman" in result.stdout
    assert "candlepin" in result.stdout
