import json

import pytest

CONTENT_TYPE_FEATURES = ('content/rpm', 'content/deb', 'content/ansible', 'content/python', 'content/container')


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
        '"export": list(settings.ALLOWED_EXPORT_PATHS), '
        '"rhsm_url": settings.SMART_PROXY_RHSM_URL}))'
    )
    result = server.run(f"podman exec pulp-api pulpcore-manager shell -c '{py}'")
    assert result.succeeded, f"Failed to read Pulp settings: {result.stderr}"
    return json.loads(result.stdout)


def test_pulp_rhsm_url_set_on_content_proxy(pulp_settings, server_fqdn):
    assert pulp_settings['rhsm_url'] == f'https://{server_fqdn}/rhsm'


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


@pytest.mark.parametrize('feature', [
    pytest.param(feature, marks=pytest.mark.feature(feature), id=feature)
    for feature in CONTENT_TYPE_FEATURES
])
def test_pulp_smart_proxy_content_type_feature(pulp_smart_proxy_features, feature):
    capability = feature.removeprefix('content/')
    assert capability in pulp_smart_proxy_features['pulpcore'].get('capabilities', [])


@pytest.mark.parametrize('capability', ('core', 'smart_proxy', 'file', 'certguard'))
def test_pulp_smart_proxy_base_capability(pulp_smart_proxy_features, capability):
    assert capability in pulp_smart_proxy_features['pulpcore'].get('capabilities', [])


def test_pulp_api_status(curl_request):
    cmd = curl_request("pulp/api/v3/status/")
    assert cmd.succeeded
    assert cmd.stdout == '200'
