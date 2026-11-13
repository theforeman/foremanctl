import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def _restart_tasks(tasks):
    for task in tasks:
        if task.get('ansible.builtin.systemd', {}).get('state') == 'restarted':
            yield task
        yield from _restart_tasks(task.get('block', []))


def test_image_pulls_wait_for_service_completion(tmp_path):
    role = Path(__file__).resolve().parents[2] / 'src/roles/images/tasks/pull.yaml'
    tasks = list(_restart_tasks(yaml.safe_load(role.read_text())))
    assert len(tasks) == 1
    task = dict(tasks[0])

    # Replace the systemd operation, preserving the actual loop/async/poll controls.
    del task['ansible.builtin.systemd']
    task['ansible.builtin.command'] = {'argv': [sys.executable, '-c', 'pass']}
    task['register'] = 'image_pull_results'
    playbook = [{
        'hosts': 'localhost',
        'gather_facts': False,
        'vars': {
            'ansible_python_interpreter': sys.executable,
            'ansible_async_dir': str(tmp_path / 'async'),
            'images_deployed_names': ['first', 'second'],
            'images_pull_timeout': 600,
        },
        'tasks': [task, {
            'name': 'Verify each restart was awaited',
            'ansible.builtin.assert': {'that': ['item.finished == 1', 'item.rc == 0']},
            'loop': '{{ image_pull_results.results }}',
        }],
    }]
    path = tmp_path / 'pulls.yaml'
    path.write_text(yaml.safe_dump(playbook))
    config = tmp_path / 'ansible.cfg'
    config.write_text('[defaults]\nretry_files_enabled = False\n')
    command = shutil.which('ansible-playbook')
    assert command, 'ansible-playbook must be installed in the test environment'

    result = subprocess.run(
        [command, '-i', 'localhost,', '-c', 'local', str(path)],
        env=os.environ | {
            'ANSIBLE_CONFIG': str(config),
            'ANSIBLE_HOME': str(tmp_path / 'home'),
            'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'local'),
        },
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
