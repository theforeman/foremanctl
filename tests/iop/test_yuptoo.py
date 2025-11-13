import pytest


def test_yuptoo_service(server):
    service = server.service("iop-core-yuptoo")
    assert service.is_running
    assert service.is_enabled


def test_yuptoo_port(server):
    addr = server.addr("localhost")
    assert addr.port("5005").is_reachable


def test_yuptoo_container_running(server):
    result = server.run("podman inspect iop-core-yuptoo --format '{{.State.Status}}'")
    assert result.succeeded
    assert "running" in result.stdout


def test_yuptoo_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-core-yuptoo.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_yuptoo_service_dependencies(server):
    result = server.run("systemctl show iop-core-yuptoo --property=After")
    assert result.succeeded
    assert "iop-core-kafka.service" in result.stdout


def test_yuptoo_http_endpoint(server):
    result = server.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:5005/")
    assert result.succeeded
    assert "200" in result.stdout
