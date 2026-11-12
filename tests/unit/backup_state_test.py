import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

BACKUP_TASKS = Path(__file__).resolve().parents[2] / 'src' / 'roles' / 'backup' / 'tasks' / 'main.yaml'


@pytest.mark.skipif(shutil.which('ansible-playbook') is None, reason='ansible-core is required')
@pytest.mark.parametrize('incremental', [False, True], ids=['full', 'incremental'])
def test_backup_state_with_existing_snapshot(tmp_path, incremental):
    state = tmp_path / 'foremanctl'
    state.mkdir()
    (state / 'parameters.yaml').write_text('flavor: katello\n')
    subprocess.run([
        'tar', '-czf', str(tmp_path / 'previous.tar.gz'),
        f'--listed-incremental={tmp_path / "config.snar"}', '-C', str(tmp_path), state.name,
    ], check=True)
    (state / 'new-file').touch()

    archive_task = next(
        task
        for block in yaml.safe_load(BACKUP_TASKS.read_text())
        for task in block.get('block', [])
        if task['name'] == 'Backup foremanctl state directory'
    )
    variables = {'obsah_state_path': str(state)}
    if incremental:
        variables['backup_incremental'] = str(tmp_path / 'base-backup')
    playbook = tmp_path / 'archive.yaml'
    playbook.write_text(yaml.safe_dump([{
        'hosts': 'localhost',
        'connection': 'local',
        'gather_facts': False,
        'vars': variables,
        'tasks': [archive_task],
    }]))

    result = subprocess.run(
        ['ansible-playbook', '-i', 'localhost,', str(playbook)],
        env=dict(os.environ, ANSIBLE_STDOUT_CALLBACK='default', ANSIBLE_FORCE_COLOR='0'),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    members = subprocess.check_output(
        ['tar', '-tzf', str(tmp_path / 'foremanctl-state.tar.gz')], text=True
    ).splitlines()
    assert 'foremanctl/new-file' in members
    if incremental:
        assert 'foremanctl/parameters.yaml' not in members
    else:
        assert 'foremanctl/parameters.yaml' in members
