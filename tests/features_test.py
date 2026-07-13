import subprocess


def test_foremanctl_features(available_features):
    command = ['./foremanctl', 'features']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    for noise in ['PLAY [', 'TASK [', 'ok:', 'changed:', 'PLAY RECAP']:
        assert noise not in result.stdout, f"Ansible output not suppressed: found '{noise}'"

    for feature in available_features:
        assert feature in result.stdout, f"Expected feature '{feature}' in output"


def test_foremanctl_features_list_enabled(enabled_features):
    command = ['./foremanctl', 'features', '--list-enabled']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    for feature in enabled_features:
        assert feature in result.stdout, f"Expected feature '{feature}' in output"


def test_invalid_feature_rejected():
    command = ['./foremanctl', 'deploy', '--add-feature', 'invalid-feature']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 2

    assert 'Unknown feature(s) requested: invalid-feature' in result.stdout
    assert "Run 'foremanctl features' to list all available features." in result.stdout
