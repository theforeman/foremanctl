import datetime
import json

import pytest

FOREMAN_PROXY_PORT = 8443


@pytest.fixture(scope="module")
def proxy_v2_features(server, certificates, server_fqdn):
    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/v2/features"
    )
    assert cmd.succeeded, f"Failed to query /v2/features: {cmd.stderr}"
    return json.loads(cmd.stdout)


def test_foreman_proxy_features(server, certificates, server_fqdn, enabled_features):
    cmd = server.run(f"curl --cacert {certificates['server_ca_certificate']} --silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features")
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "logs" in features
    assert "script" in features
    assert "dynflow" in features
    if 'bmc' in enabled_features:
        assert "bmc" in features
    else:
        assert "bmc" not in features
    if 'dns' in enabled_features:
        assert "dns" in features
    else:
        assert "dns" not in features


def test_foreman_proxy_service(server):
    foreman_proxy = server.service("foreman-proxy")
    assert foreman_proxy.is_running


def test_foreman_proxy_port(server):
    foreman_proxy = server.addr('localhost')
    assert foreman_proxy.port(FOREMAN_PROXY_PORT).is_reachable


@pytest.mark.xfail(reason='Fails until report feature is available')
def test_foreman_proxy_client_auth_to_foreman(server, certificates, server_fqdn):
    test_report = {"config_report": {"host": "test.example.com", "reported_at": datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}}
    cmd = server.run(
        f"curl --cacert {certificates['server_ca_certificate']} "
        f"--cert {certificates['client_certificate']} "
        f"--key {certificates['client_key']} "
        f"--output /dev/null --write-out '%{{http_code}}' "
        f"--data '{json.dumps(test_report)}' --header 'Content-Type: application/json' "
        f"https://{server_fqdn}/api/v2/config_reports"
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
