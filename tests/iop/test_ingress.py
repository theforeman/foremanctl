import pytest


def test_ingress_service(server):
    service = server.service("iop-core-ingress")
    assert service.is_running
    assert service.is_enabled


def test_ingress_port(server):
    addr = server.addr("localhost")
    assert addr.port("8080").is_reachable


def test_ingress_container_running(server):
    result = server.run("podman inspect iop-core-ingress --format '{{.State.Status}}'")
    assert result.succeeded
    assert "running" in result.stdout


def test_ingress_quadlet_file(server):
    quadlet_file = server.file("/etc/containers/systemd/iop-core-ingress.container")
    assert quadlet_file.exists
    assert quadlet_file.is_file


def test_ingress_http_endpoint(server):
    result = server.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/")
    assert result.succeeded
    assert "200" in result.stdout
