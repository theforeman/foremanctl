import pytest

pytestmark = pytest.mark.feature("iop")


def test_iop_core_kafka_service(server):
    service = server.service("iop-core-kafka")
    assert service.is_running
    assert service.is_enabled


def test_iop_core_ingress_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-ingress").succeeded
    if service_exists:
        service = server.service("iop-core-ingress")
        assert service.is_running
        assert service.is_enabled


def test_iop_ingress_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-core-ingress:8080/")
    assert result.succeeded


def test_iop_core_puptoo_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-puptoo").succeeded
    if service_exists:
        service = server.service("iop-core-puptoo")
        assert service.is_running
        assert service.is_enabled


def test_iop_puptoo_metrics_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-core-puptoo:8000/metrics")
    assert result.succeeded


def test_iop_core_yuptoo_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-yuptoo").succeeded
    if service_exists:
        service = server.service("iop-core-yuptoo")
        assert service.is_running
        assert service.is_enabled


def test_iop_yuptoo_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-core-yuptoo:5005/")
    assert result.succeeded


def test_iop_core_engine_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-engine").succeeded
    if service_exists:
        service = server.service("iop-core-engine")
        assert service.is_running
        assert service.is_enabled


def test_iop_core_gateway_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-gateway").succeeded
    if service_exists:
        service = server.service("iop-core-gateway")
        assert service.is_running
        assert service.is_enabled


def test_iop_gateway_endpoint(server):
    result = server.run("curl --fail -s -o /dev/null http://localhost:24443/")
    assert result.succeeded


def test_iop_gateway_api_ingress_endpoint(server):
    result = server.run("curl --fail -s -o /dev/null http://localhost:24443/api/ingress")
    assert result.succeeded


def test_iop_gateway_https_cert_auth(server, certificates):
    result = server.run(f"curl --fail -s -o /dev/null https://localhost:24443/ --cert {certificates['iop_gateway_client_certificate']} --key {certificates['iop_gateway_client_key']} --cacert {certificates['iop_gateway_client_ca_certificate']}")
    assert result.succeeded


def test_iop_core_host_inventory_api_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-host-inventory-api").succeeded
    if service_exists:
        service = server.service("iop-core-host-inventory-api")
        assert service.is_running
        assert service.is_enabled


def test_iop_inventory_mq_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-core-host-inventory:9126/")
    assert result.succeeded


def test_iop_inventory_api_health_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-core-host-inventory-api:8081/health")
    assert result.succeeded


def test_iop_service_advisor_backend_api_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-service-advisor-backend-api").succeeded
    if service_exists:
        service = server.service("iop-service-advisor-backend-api")
        assert service.is_running
        assert service.is_enabled


def test_iop_service_advisor_backend_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-service-advisor-backend-service").succeeded
    if service_exists:
        service = server.service("iop-service-advisor-backend-service")
        assert service.is_running
        assert service.is_enabled


def test_iop_advisor_api_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-service-advisor-backend-api:8000/api/insights/v1/status/live/")
    assert result.succeeded


def test_iop_service_remediations_api_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-service-remediations-api").succeeded
    if service_exists:
        service = server.service("iop-service-remediations-api")
        assert service.is_running
        assert service.is_enabled


def test_iop_remediations_api_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-gateway')} curl --fail -s -o /dev/null http://iop-service-remediations-api:9002/health")
    assert result.succeeded
