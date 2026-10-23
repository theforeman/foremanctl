import pytest
import yaml


def test_container_gateway_running(proxy_v2_features):
    """Verify container_gateway is loaded and running via /v2/features."""
    assert proxy_v2_features['container_gateway']['state'] == 'running'


@pytest.mark.parametrize('setting', ['db_max_connections', 'db_pool_timeout'])
def test_container_gateway_database_pool_settings(server, obsah_params, setting):
    """Verify database pool settings reach the configuration mounted in the proxy."""
    config = yaml.safe_load(server.check_output(
        'podman exec foreman-proxy cat /etc/foreman-proxy/settings.d/container_gateway.yml'
    ))
    expected = int(obsah_params.get(f'foreman_proxy_container_gateway_{setting}', 30))
    assert config[f':{setting}'] == expected


@pytest.fixture
def podman_login(server, server_fqdn):
    """Login to the container registry and logout after the test."""
    result = server.run("podman login %s --username admin --password changeme --tls-verify=false", server_fqdn)
    yield result
    server.run("podman logout %s", server_fqdn)


def test_container_gateway_podman_login(podman_login):
    """Verify podman can authenticate to the container registry via the container gateway."""
    assert podman_login.succeeded, f"podman login failed: {podman_login.stderr}"
    assert "Login Succeeded" in podman_login.stdout
