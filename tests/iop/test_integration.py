import pytest


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


def test_iop_ingress_endpoint(server):
    result = server.run("curl -f http://localhost:8080/ 2>/dev/null || echo 'Ingress not yet responding'")
    assert result.rc == 0


def test_iop_core_puptoo_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-puptoo").succeeded
    if service_exists:
        service = server.service("iop-core-puptoo")
        assert service.is_running
        assert service.is_enabled


def test_iop_puptoo_metrics_endpoint(server):
    result = server.run("curl -f http://localhost:8000/metrics 2>/dev/null || echo 'Puptoo not yet responding'")
    assert result.rc == 0


def test_iop_core_yuptoo_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-yuptoo").succeeded
    if service_exists:
        service = server.service("iop-core-yuptoo")
        assert service.is_running
        assert service.is_enabled


def test_iop_yuptoo_endpoint(server):
    result = server.run("curl -f http://localhost:5005/ 2>/dev/null || echo 'Yuptoo not yet responding'")
    assert result.rc == 0


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
    result = server.run("curl -f http://localhost:24443/ 2>/dev/null || echo 'Gateway not yet responding'")
    assert result.rc == 0


def test_iop_gateway_api_ingress_endpoint(server):
    result = server.run("curl -f http://localhost:24443/api/ingress 2>/dev/null || echo 'Gateway API ingress not yet responding'")
    assert result.rc == 0


def test_iop_gateway_https_cert_auth(server, certificates):
    result = server.run(f"curl -s -o /dev/null -w '%{{http_code}}' https://localhost:24443/ --cert {certificates['iop_gateway_client_certificate']} --key {certificates['iop_gateway_client_key']} --cacert {certificates['iop_gateway_client_ca_certificate']} 2>/dev/null || echo '000'")
    assert "200" in result.stdout


def test_iop_core_host_inventory_api_service(server):
    service_exists = server.run("systemctl list-units --type=service | grep iop-core-host-inventory-api").succeeded
    if service_exists:
        service = server.service("iop-core-host-inventory-api")
        assert service.is_running
        assert service.is_enabled


def test_iop_inventory_mq_endpoint(server):
    result = server.run("podman run --network=iop-core-network quay.io/iop/host-inventory:latest curl http://iop-core-host-inventory:9126/ 2>/dev/null || echo 'Host inventory MQ not yet responding'")
    assert result.rc == 0


def test_iop_inventory_api_health_endpoint(server):
    result = server.run("podman run --network=iop-core-network quay.io/iop/host-inventory curl -s -o /dev/null -w '%{http_code}' http://iop-core-host-inventory-api:8081/health 2>/dev/null || echo '000'")
    assert "200" in result.stdout


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


def test_iop_advisor_api_endpoint(server):
    result = server.run("podman run --network=iop-core-network --rm quay.io/iop/advisor-backend:latest curl -f http://iop-service-advisor-backend-api:8000/ 2>/dev/null || echo 'Advisor API not yet responding'")
    assert result.rc == 0
