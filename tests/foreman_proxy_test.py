import datetime
import json
import pytest

FOREMAN_PROXY_PORT = 8443

def test_foreman_proxy_features(server, certificates, server_fqdn):
    cmd = server.run(f"curl --cacert {certificates['server_ca_certificate']} --silent https://{server_fqdn}:{FOREMAN_PROXY_PORT}/features")
    assert cmd.succeeded
    features = json.loads(cmd.stdout)
    assert "logs" in features
    assert "script" in features
    assert "dynflow" in features

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
