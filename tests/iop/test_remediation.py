import pytest

pytestmark = pytest.mark.feature("iop")


def test_remediation_api_service(server):
    service = server.service("iop-service-remediations-api")
    assert service.is_running
    assert service.is_enabled


def test_remediation_api_service_dependencies(server):
    result = server.run("systemctl show iop-service-remediations-api --property=After")
    assert result.succeeded
    assert "iop-core-host-inventory-api.service" in result.stdout
    assert "iop-service-advisor-backend-api.service" in result.stdout


def test_remediation_api_environment_variables(server):
    result = server.run("podman inspect iop-service-remediations-api --format '{{.Config.Env}}'")
    assert result.succeeded
    assert "REDIS_ENABLED=false" in result.stdout
    assert "RBAC_ENFORCE=false" in result.stdout
    assert "DB_SSL_ENABLED=false" in result.stdout


def test_remediation_api_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-remediation')} curl --fail -s -o /dev/null http://iop-service-remediations-api:9002/health")
    assert result.succeeded
