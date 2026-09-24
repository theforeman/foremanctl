import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

TEST_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = TEST_DIR.parent.parent


def _run_feature_checks(tmp_path, enabled_features, database_mode, installed=False, existing_iop=False):
    installed_flag = tmp_path / '.installed'
    if installed:
        installed_flag.touch()
    iop_marker = tmp_path / 'iop-core-gateway.container'
    if existing_iop:
        iop_marker.touch()

    playbook_path = tmp_path / 'check-features.yml'
    playbook_path.write_text(
        yaml.safe_dump([
            {
                'name': 'Check feature configuration',
                'hosts': 'localhost',
                'gather_facts': False,
                'roles': ['check_features'],
                'vars': {
                    'features': [],
                    'enabled_features': enabled_features,
                    'database_mode': database_mode,
                    'check_features_installed_flag': str(installed_flag),
                    'check_features_iop_marker': str(iop_marker),
                },
            },
        ]),
        encoding='utf-8',
    )
    environment = os.environ | {
        'ANSIBLE_FILTER_PLUGINS': str(REPOSITORY_ROOT / 'src' / 'filter_plugins'),
        'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible-tmp'),
        'ANSIBLE_ROLES_PATH': str(REPOSITORY_ROOT / 'src' / 'roles'),
        'ANSIBLE_STDOUT_CALLBACK': 'default',
    }
    ansible_playbook = shutil.which('ansible-playbook') or Path(sys.executable).with_name('ansible-playbook')
    return subprocess.run(
        [
            str(ansible_playbook),
            '--inventory', 'localhost,',
            '--connection', 'local',
            str(playbook_path),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_iop_rejects_external_database(tmp_path):
    result = _run_feature_checks(tmp_path, ['iop'], 'external')

    assert result.returncode != 0
    assert 'IOP requires the internal database mode.' in result.stdout


def test_iop_accepts_internal_database(tmp_path):
    result = _run_feature_checks(tmp_path, ['iop'], 'internal')

    assert result.returncode == 0, result.stdout + result.stderr


def test_external_database_without_iop_is_accepted(tmp_path):
    result = _run_feature_checks(tmp_path, ['foreman'], 'external')

    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_iop_external_database_is_not_blocked(tmp_path):
    result = _run_feature_checks(tmp_path, ['iop'], 'external', installed=True, existing_iop=True)

    assert result.returncode == 0, result.stdout + result.stderr


def test_installed_external_database_rejects_new_iop(tmp_path):
    result = _run_feature_checks(tmp_path, ['iop'], 'external', installed=True)

    assert result.returncode != 0
    assert 'IOP requires the internal database mode.' in result.stdout
