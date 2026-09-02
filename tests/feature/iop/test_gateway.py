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


def test_gateway_relay_reaches_foreman(server, iop_image):
    # Regression test for https://github.com/theforeman/foremanctl/issues/467:
    # the relay used to send "Host: localhost" to Foreman, which Rails'
    # ActionDispatch::HostAuthorization rejected with a 403 before the
    # request reached the app. The Katello organizations endpoint is a
    # convenient real-world path that is relayed through the gateway and
    # only succeeds once the Host header matches Foreman's allowed hosts.
    result = server.run(
        f"podman run --network=iop-core-network --rm {iop_image('iop-inventory')} "
        "curl -s -o /dev/null -w '%{http_code}' http://iop-core-gateway:9090/katello/api/v2/organizations"
    )
    assert "200" in result.stdout
