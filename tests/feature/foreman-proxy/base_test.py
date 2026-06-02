import datetime
import json

import pytest
import yaml

from tests.conftest import FOREMAN_PROXY_PORT


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
    if 'container-gateway' in enabled_features:
        assert "container_gateway" in features
    else:
        assert "container_gateway" not in features


def test_foreman_proxy_permitted_hosts_config(server, server_fqdn, obsah_params):
    cmd = server.run(
        "podman secret inspect "
        "--format '{{.SecretData}}' "
        "--showsecret foreman-proxy-settings-yml"
    )
    assert cmd.succeeded

    settings = yaml.safe_load(cmd.stdout)
    expected_hosts = [server_fqdn] + (obsah_params.get('server_aliases') or [])
    assert settings[':permitted_hosts'] == expected_hosts


def test_foreman_proxy_host_injection(curl_request, server):
    warning = 'permitted_hosts is configured but not enforced by this Sinatra version'
    invocation_id = server.check_output(
        "systemctl show foreman-proxy.service --property=InvocationID --value"
    ).strip()
    assert invocation_id, "Could not determine the current foreman-proxy service invocation"

    journal = server.run(
        f"journalctl -u foreman-proxy _SYSTEMD_INVOCATION_ID={invocation_id} --no-pager"
    )
    assert journal.succeeded, f"Failed to read foreman-proxy startup journal: {journal.stderr}"
    if warning in journal.stdout:
        pytest.skip("Host-header rejection is not supported by the installed Sinatra version")

    host = 'evil.hackers.test'
    request = {
        'base_url': f"https://{host}:{FOREMAN_PROXY_PORT}",
        'headers': {"Host": host},
        'resolve': f"{host}:{FOREMAN_PROXY_PORT}:127.0.0.1",
        'insecure': True,
    }
    status = curl_request("v2/features", **request)
    assert status.succeeded, f"Failed to query Foreman Proxy: {status.stderr}"
    assert status.stdout.strip() == '403', f"Expected HTTP 403, got {status.stdout.strip()}"

    body = curl_request("v2/features", return_body=True, **request)
    assert body.succeeded, f"Failed to query Foreman Proxy: {body.stderr}"
    assert body.stdout.strip() == 'Host not permitted'


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


@pytest.mark.feature('dns')
def test_dns_provider(proxy_v2_features):
    settings = proxy_v2_features['dns'].get('settings', {})
    assert settings.get('use_provider') == 'dns_nsupdate'


@pytest.mark.feature('dns')
@pytest.mark.parametrize('dns_name,dns_value,dns_type', [
    ('test-v4.example.test', '192.0.2.100', 'A'),
    ('test-v6.example.test', '2001:db8::1', 'AAAA'),
    ('test-cname.example.test', 'test.example.test', 'CNAME'),
    ('reverse-v4.example.test', '100.2.0.192.in-addr.arpa', 'PTR'),
    ('reverse-v6.example.test', '0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa', 'PTR')
])
def test_dns_nsupdate(server, certificates, server_fqdn, dns_name, dns_value, dns_type):

    def dns_cmd(curl_opts, extra_url=""):
        return server.run(
            f"curl --cacert {certificates['server_ca_certificate']} "
            f"--cert {certificates['client_certificate']} "
            f"--key {certificates['client_key']} "
            f"--output /dev/null --write-out '%{{http_code}}' "
            f"{curl_opts} "
            f"https://{server_fqdn}:8443/dns/{extra_url}"
        )

    if dns_type == 'PTR':
        expected = f"{dns_name}."
        query = dns_value
    elif dns_type == 'CNAME':
        expected = f"{dns_value}."
        query = dns_name
    else:
        expected = dns_value
        query = dns_name

    create_cmd = dns_cmd(f"--data 'fqdn={dns_name}&value={dns_value}&type={dns_type}'")
    assert create_cmd.succeeded
    assert create_cmd.stdout == '200'

    verify_cmd = server.run(f"dig +short {query} {dns_type} @named.example.com")
    assert verify_cmd.succeeded
    assert verify_cmd.stdout.strip() == expected

    delete_cmd = dns_cmd("-X DELETE", f"{query}/{dns_type}")
    assert delete_cmd.succeeded
    assert delete_cmd.stdout == '200'

    verify_cmd = server.run(f"dig +short {query} {dns_type} @named.example.com")
    assert verify_cmd.succeeded
    assert verify_cmd.stdout.strip() == ""
