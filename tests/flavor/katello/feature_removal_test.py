import os
import subprocess
from pathlib import Path

import yaml

PARAMETERS_FILE = Path(os.environ.get('OBSAH_STATE', '.var/lib/foremanctl')) / 'parameters.yaml'


def _deploy(*arguments):
    return subprocess.run(
        ['./foremanctl', 'deploy', *arguments],
        capture_output=True,
        text=True,
    )


def _features():
    if not PARAMETERS_FILE.exists():
        return []
    with PARAMETERS_FILE.open() as parameters_file:
        return (yaml.safe_load(parameters_file) or {}).get('features', [])


def test_feature_add_remove_and_readd_persist_across_invocations():
    original_state = PARAMETERS_FILE.read_bytes() if PARAMETERS_FILE.exists() else None
    initially_enabled = 'bmc' in _features()

    try:
        add_result = _deploy('--add-feature', 'bmc')
        assert add_result.returncode == 0, add_result.stderr
        assert 'bmc' in _features()

        remove_result = _deploy('--remove-feature', 'bmc')
        assert remove_result.returncode == 0, remove_result.stderr
        assert 'bmc' not in _features()

        with PARAMETERS_FILE.open() as parameters_file:
            persisted = yaml.safe_load(parameters_file) or {}
        assert 'remove_features' not in persisted

        readd_result = _deploy('--add-feature', 'bmc')
        assert readd_result.returncode == 0, readd_result.stderr
        assert 'bmc' in _features()
    finally:
        try:
            if not initially_enabled:
                cleanup_result = _deploy('--remove-feature', 'bmc')
                assert cleanup_result.returncode == 0, cleanup_result.stderr
        finally:
            if original_state is None:
                PARAMETERS_FILE.unlink(missing_ok=True)
            else:
                PARAMETERS_FILE.write_bytes(original_state)
