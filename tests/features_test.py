import subprocess

import pytest

DEFAULT_FEATURES = {
    'ansible',
    'azure-rm',
    'bmc',
    'candlepin',
    'content/ansible',
    'content/container',
    'content/deb',
    'content/python',
    'content/rpm',
    'dynflow',
    'foreman',
    'foreman-proxy',
    'google',
    'hammer',
    'httpd',
    'katello',
    'pulp',
    'remote-execution',
    'tasks',
    'valkey',
    'webhooks',
}

EXPECTED_FEATURES = {
    'default': DEFAULT_FEATURES,
    'default-iop': DEFAULT_FEATURES | {'iop', 'rh-cloud'},
    'upgrade': DEFAULT_FEATURES - {'ansible', 'webhooks'},
    'migration': DEFAULT_FEATURES,
    'proxy': {
        'bmc',
        'container-gateway',
        'content/ansible',
        'content/container',
        'content/deb',
        'content/python',
        'content/rpm',
        'foreman-proxy',
        'httpd',
        'pulp',
        'registration',
        'templates',
        'valkey',
    },
    'satellite': (DEFAULT_FEATURES | {'rh-cloud', 'theme-satellite'}) - {'content/python', 'content/deb'},
    'capsule': {
        'bmc',
        'container-gateway',
        'content/ansible',
        'content/container',
        'content/rpm',
        'foreman-proxy',
        'httpd',
        'pulp',
        'registration',
        'templates',
        'valkey',
    },
}


def test_foremanctl_features(available_features):
    command = ['./foremanctl', 'features']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    for noise in ['PLAY [', 'TASK [', 'ok:', 'changed:', 'PLAY RECAP']:
        assert noise not in result.stdout, f"Ansible output not suppressed: found '{noise}'"

    for feature in available_features:
        assert feature in result.stdout, f"Expected feature '{feature}' in output"


def test_foremanctl_features_list_enabled(user_enabled_features):
    command = ['./foremanctl', 'features', '--list-enabled']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    for feature in user_enabled_features:
        assert feature in result.stdout, f"Expected feature '{feature}' in output"


def test_invalid_feature_rejected():
    command = ['./foremanctl', 'deploy', '--add-feature', 'invalid-feature']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 2

    assert 'Unknown feature(s) requested: invalid-feature' in result.stdout
    assert "Run 'foremanctl features' to list all available features." in result.stdout


def test_enabled_features(pytestconfig, enabled_features):
    featureset = pytestconfig.getoption("featureset")
    if featureset is None:
        pytest.skip("No featureset to compare against was provided")

    expected_features = EXPECTED_FEATURES.get(featureset)
    assert expected_features, f"Unknown featureset: {featureset}"

    assert expected_features == enabled_features, "The set of enabled features does not match expectations. Update EXPECTED_FEATURES if the change is intentional."
