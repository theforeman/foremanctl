def test_ingress_service(server):
    service = server.service("iop-core-ingress")
    assert service.is_running
    assert service.is_enabled


def test_ingress_http_endpoint(server, iop_image):
    result = server.run(f"podman run --network=iop-core-network --rm {iop_image('iop-ingress')} curl --fail -s -o /dev/null http://iop-core-ingress:8080/")
    assert result.succeeded
