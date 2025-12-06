import pytest


def test_gateway_service(server):
    service = server.service("iop-core-gateway")
    assert service.is_running
    assert service.is_enabled


def test_gateway_port(server):
    addr = server.addr("localhost")
    assert addr.port("24443").is_reachable


def test_gateway_secrets(server):
    secrets = [
        'iop-core-gateway-server-cert',
        'iop-core-gateway-server-key',
        'iop-core-gateway-server-ca-cert',
        'iop-core-gateway-client-cert',
        'iop-core-gateway-client-key',
        'iop-core-gateway-client-ca-cert',
        'iop-core-gateway-relay-conf'
    ]

    result = server.run("podman secret ls --format '{{.Name}}'")
    assert result.succeeded

    for secret_name in secrets:
        assert secret_name in result.stdout