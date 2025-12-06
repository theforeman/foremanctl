import pytest


def test_ingress_service(server):
    service = server.service("iop-core-ingress")
    assert service.is_running
    assert service.is_enabled


def test_ingress_http_endpoint(server):
    result = server.run("podman run --rm quay.io/iop/ingress:latest curl -s -o /dev/null -w '%{http_code}' http://iop-core-ingress:8080/")
    if result.succeeded:
        assert "200" in result.stdout