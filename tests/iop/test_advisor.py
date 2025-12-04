import pytest


def test_advisor_backend_api_service(server):
    service = server.service("iop-service-advisor-backend-api")
    assert service.is_running
    assert service.is_enabled


def test_advisor_backend_service(server):
    service = server.service("iop-service-advisor-backend-service")
    assert service.is_running
    assert service.is_enabled


def test_advisor_api_container(server):
    result = server.run("podman ps --format '{{.Names}}' | grep iop-service-advisor-backend-api")
    assert result.succeeded
    assert "iop-service-advisor-backend-api" in result.stdout


def test_advisor_service_container(server):
    result = server.run("podman ps --format '{{.Names}}' | grep iop-service-advisor-backend-service")
    assert result.succeeded
    assert "iop-service-advisor-backend-service" in result.stdout


def test_advisor_api_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-service-advisor-backend-api.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_advisor_service_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-service-advisor-backend-service.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_advisor_api_service_dependencies(server):
    result = server.run("systemctl show iop-service-advisor-backend-api --property=After")
    assert result.succeeded
    assert "iop-core-kafka.service" in result.stdout


def test_advisor_service_dependencies(server):
    result = server.run("systemctl show iop-service-advisor-backend-service --property=After")
    assert result.succeeded
    assert "iop-core-kafka.service" in result.stdout


def test_advisor_database_secrets(server):
    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded
    assert "iop-service-advisor-backend-database-username" in result.stdout
    assert "iop-service-advisor-backend-database-password" in result.stdout
    assert "iop-service-advisor-backend-database-name" in result.stdout
    assert "iop-service-advisor-backend-database-host" in result.stdout
    assert "iop-service-advisor-backend-database-port" in result.stdout


def test_advisor_api_kafka_connectivity(server):
    result = server.run("podman logs iop-service-advisor-backend-api 2>&1 | grep -i 'kafka\\|bootstrap'")
    assert result.succeeded


def test_advisor_service_kafka_connectivity(server):
    result = server.run("podman logs iop-service-advisor-backend-service 2>&1 | grep -i 'kafka\\|bootstrap'")
    assert result.succeeded


def test_advisor_api_port_configured(server):
    result = server.run("podman inspect iop-service-advisor-backend-api --format '{{.Config.Env}}'")
    assert result.succeeded
    assert "PORT=8000" in result.stdout


def test_advisor_fdw_foreign_server_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT * FROM pg_foreign_server WHERE srvname = 'hbi_server';\"")
    assert result.succeeded
    assert "hbi_server" in result.stdout


def test_advisor_fdw_user_mapping_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT * FROM information_schema.user_mappings WHERE foreign_server_name = 'hbi_server';\"")
    assert result.succeeded
    assert "advisor_user" in result.stdout


def test_advisor_fdw_foreign_table_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"\\det inventory_source.*\"")
    assert result.succeeded
    assert "hosts" in result.stdout


def test_advisor_fdw_inventory_view_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"\\dv inventory.*\"")
    assert result.succeeded
    assert "hosts" in result.stdout


def test_advisor_fdw_inventory_view_queryable(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT 1 FROM inventory.hosts LIMIT 1;\"")
    assert result.rc == 0


# Additional comprehensive FDW tests (beyond puppet-iop baseline)
def test_advisor_fdw_postgres_fdw_extension(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT extname FROM pg_extension WHERE extname = 'postgres_fdw';\"")
    assert result.succeeded
    assert "postgres_fdw" in result.stdout


def test_advisor_fdw_postgres_user_mapping_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT usename FROM pg_user_mappings WHERE srvname = 'hbi_server' AND usename = 'postgres';\"")
    assert result.succeeded
    assert "postgres" in result.stdout


def test_advisor_fdw_inventory_source_schema_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'inventory_source';\"")
    assert result.succeeded
    assert "inventory_source" in result.stdout


def test_advisor_fdw_inventory_schema_exists(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'inventory';\"")
    assert result.succeeded
    assert "inventory" in result.stdout


def test_advisor_fdw_permissions_on_view(server):
    result = server.run("podman exec postgresql psql advisor_db -c \"SELECT privilege_type FROM information_schema.table_privileges WHERE grantee = 'advisor_user' AND table_schema = 'inventory' AND table_name = 'hosts';\"")
    assert result.succeeded
    assert "SELECT" in result.stdout


def test_advisor_api_endpoint(server):
    result = server.run("podman run --network=iop-core-network --rm quay.io/iop/advisor-backend:latest curl -s -o /dev/null -w '%{http_code}' http://iop-service-advisor-backend-api:8000/ 2>/dev/null || echo '000'")
    assert result.stdout.strip() != "000"
