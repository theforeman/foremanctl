import pytest


def test_puptoo_service(server):
    service = server.service("iop-core-puptoo")
    assert service.is_running
    assert service.is_enabled


def test_puptoo_port(server):
    addr = server.addr("localhost")
    assert addr.port("8000").is_reachable


def test_puptoo_container_running(server):
    result = server.run("podman inspect iop-core-puptoo --format '{{.State.Status}}'")
    assert result.succeeded
    assert "running" in result.stdout


def test_puptoo_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-core-puptoo.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_puptoo_service_dependencies(server):
    result = server.run("systemctl show iop-core-puptoo --property=After")
    assert result.succeeded
    assert "iop-core-kafka.service" in result.stdout


def test_puptoo_http_endpoint(server):
    result = server.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/metrics")
    assert result.succeeded
    assert "200" in result.stdout


def test_puptoo_kafka_connectivity(server):
    result = server.run("podman logs iop-core-puptoo 2>&1 | grep -i 'kafka\\|bootstrap'")
    assert result.succeeded
