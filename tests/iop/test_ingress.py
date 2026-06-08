import pytest

pytestmark = pytest.mark.feature("iop")


def test_ingress_service(server):
    service = server.service("iop-core-ingress")
    assert service.is_running
    assert service.is_enabled


def test_ingress_http_endpoint(server, iop_image):
    result = server.run(f"podman run --rm {iop_image('iop-ingress')} curl -s -o /dev/null -w '%{{http_code}}' http://iop-core-ingress:8080/")
    if result.succeeded:
        assert "200" in result.stdout
