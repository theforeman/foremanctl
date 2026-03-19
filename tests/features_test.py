import subprocess

def test_foremanctl_features():
    command = ['./foremanctl', 'features']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    for noise in ['PLAY [', 'TASK [', 'ok:', 'changed:', 'PLAY RECAP']:
        assert noise not in result.stdout, f"Ansible output not suppressed: found '{noise}'"

    for feature in ['foreman', 'foreman-proxy', 'azure-rm']:
        assert feature in result.stdout, f"Expected feature '{feature}' in output"

def test_foremanctl_features_list_enabled():
    command = ['./foremanctl', 'features', '--list-enabled']
    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode == 0

    assert 'enabled' in result.stdout
    assert 'available' not in result.stdout
