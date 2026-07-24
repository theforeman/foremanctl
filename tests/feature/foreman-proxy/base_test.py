import datetime
import json

import pytest

from tests.conftest import FOREMAN_PROXY_PORT


@pytest.fixture(scope="module")
def proxy_v2_features(curl_request, proxy_base_url):
    cmd = curl_request("v2/features", base_url=proxy_base_url, return_body=True)
    assert cmd.succeeded, f"Failed to query /v2/features: {cmd.stderr}"
    return json.loads(cmd.stdout)


def test_foreman_proxy_features(curl_request, proxy_base_url, enabled_features):
    cmd = curl_request("features", base_url=proxy_base_url, return_body=True)
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "logs" in features
    if 'remote-execution' in enabled_features:
        assert "script" in features
        assert "dynflow" in features
    else:
        assert "script" not in features
    if 'bmc' in enabled_features:
        assert "bmc" in features
    else:
        assert "bmc" not in features
    if 'templates' in enabled_features:
        assert "templates" in features
    else:
        assert "templates" not in features
    if 'ansible' in enabled_features:
        assert "ansible" in features
    else:
        assert "ansible" not in features
    if 'registration' in enabled_features:
        assert "registration" in features
        assert "templates" in features
    else:
        assert "registration" not in features


def test_foreman_proxy_service(server):
    foreman_proxy = server.service("foreman-proxy")
    assert foreman_proxy.is_running


def test_foreman_proxy_port(server):
    foreman_proxy = server.addr('localhost')
    assert foreman_proxy.port(FOREMAN_PROXY_PORT).is_reachable


@pytest.mark.feature('remote-execution')
def test_remote_execution_ssh_public_key_comment(server, server_fqdn):
    cmd = server.run(
        "podman secret inspect "
        "--format '{{.SecretData}}' "
        "--showsecret foreman_proxy-remote_execution_ssh-id_rsa_foreman_proxy-pub"
    )
    assert cmd.succeeded
    public_key = cmd.stdout.split()
    assert len(public_key) == 3
    assert public_key[2] == f"foreman-proxy@{server_fqdn}"


@pytest.mark.xfail(reason='Fails until report feature is available')
def test_foreman_proxy_client_auth_to_foreman(curl_request):
    test_report = {"config_report": {"host": "test.example.com", "reported_at": datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}}
    cmd = curl_request(
        "api/v2/config_reports",
        method="POST",
        data=json.dumps(test_report),
        headers={"Content-Type": "application/json"},
    )
    assert cmd.succeeded
    assert cmd.stdout == '201'


@pytest.mark.feature('bmc')
def test_bmc_capabilities(proxy_v2_features):
    assert 'bmc' in proxy_v2_features
    capabilities = proxy_v2_features['bmc'].get('capabilities', [])
    assert 'ipmitool' in capabilities
    assert 'freeipmi' in capabilities
    assert 'redfish' in capabilities


@pytest.mark.feature('bmc')
def test_bmc_default_provider(proxy_v2_features):
    settings = proxy_v2_features['bmc'].get('settings', {})
    assert settings.get('bmc_default_provider') == 'ipmitool'


@pytest.mark.feature('templates')
def test_templates_fetch_template_url(proxy_v2_features, obsah_params):
    assert 'templates' in proxy_v2_features
    settings = proxy_v2_features['templates'].get('settings', {})
    assert settings.get('template_url') == obsah_params.get('foreman_proxy_templates_url')


@pytest.mark.feature('templates')
def test_templates_endpoint_responds(curl_request, proxy_base_url, server_fqdn):
    """Fetch templateServer data from the templates proxy endpoint"""
    cmd = curl_request("unattended/templateServer", base_url=proxy_base_url, return_body=True)
    assert cmd.succeeded, f"Failed to query /unattended/templateServer: {cmd.stderr}"
    data = json.loads(cmd.stdout)
    assert 'templateServer' in data
    assert server_fqdn in data['templateServer']


@pytest.mark.feature('registration')
def test_registration_url(obsah_params):
    registration_url = obsah_params.get('foreman_proxy_registration_url')
    assert registration_url == 'https://loadbalancer.example.com:8443'


@pytest.mark.feature('registration')
def test_registration_endpoint(proxy_v2_features):
    assert 'registration' in proxy_v2_features
    assert proxy_v2_features['registration'].get('state') == 'running'
