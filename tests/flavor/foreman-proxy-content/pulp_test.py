import json

import pytest


@pytest.fixture(scope="module")
def pulp_smart_proxy_features(curl_request):
    cmd = curl_request("pulp/api/v3/smart_proxy/v2/features", return_body=True)
    assert cmd.succeeded, f"Failed to query smart_proxy features: {cmd.stderr}"
    return json.loads(cmd.stdout)


@pytest.fixture(scope="module")
def pulp_settings(server):
    py = (
        'from django.conf import settings; import json; '
        'print(json.dumps({"import": list(settings.ALLOWED_IMPORT_PATHS), '
        '"export": list(settings.ALLOWED_EXPORT_PATHS)}))'
    )
    result = server.run(f"podman exec pulp-api pulpcore-manager shell -c '{py}'")
    assert result.succeeded, f"Failed to read Pulp settings: {result.stderr}"
    return json.loads(result.stdout)


def test_import_paths_restricted(pulp_settings):
    assert [] == pulp_settings['import']
    assert '/var/lib/pulp/imports' not in pulp_settings['import']


def test_no_imports_or_exports_directories(server):
    assert not server.file("/var/lib/pulp/exports").exists
    assert not server.file("/var/lib/pulp/imports").exists


def test_pulp_smart_proxy_mirror_mode(pulp_smart_proxy_features):
    settings = pulp_smart_proxy_features['pulpcore'].get('settings', {})
    assert settings.get('mirror') is True
    assert 'client_certificate' in settings.get('client_authentication', [])


def test_pulp_smart_proxy_features(pulp_smart_proxy_features):
    features = pulp_smart_proxy_features
    assert 'pulpcore' in features
    capabilities = features['pulpcore'].get('capabilities', [])
    for expected in ('core', 'smart_proxy', 'rpm', 'deb', 'ansible', 'python', 'container', 'file', 'certguard'):
        assert expected in capabilities, f"Missing capability: {expected}"


def test_pulp_api_status(curl_request):
    cmd = curl_request("pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '200'
