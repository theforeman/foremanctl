import os

def test_foremanctl_features(capfd):
    result = os.system('./foremanctl features')

    captured = capfd.readouterr()
    assert result == 0

    for noise in ['PLAY [', 'TASK [', 'ok:', 'changed:', 'PLAY RECAP']:
        assert noise not in captured.out, f"Ansible output not suppressed: found '{noise}'"

    for feature in ['foreman', 'foreman-proxy', 'azure_rm']:
        assert feature in captured.out, f"Expected feature '{feature}' in output"
