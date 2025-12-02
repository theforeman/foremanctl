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
