from urllib.parse import urlparse

import yaml


def test_container_gateway_db_connection_string(server):
    result = server.run("podman exec foreman-proxy cat /etc/foreman-proxy/settings.d/container_gateway.yml")
    assert result.succeeded, f"Failed to read container_gateway.yml: {result.stderr}"
    config = yaml.safe_load(result.stdout)
    connection_string = config[':db_connection_string']
    parsed = urlparse(connection_string)
    assert parsed.scheme == 'postgresql'
    assert parsed.username == 'container_gateway'
    assert parsed.password, "password must not be empty"
    assert parsed.hostname == 'localhost'
    assert parsed.port == 5432
    assert parsed.path == '/container_gateway'
