import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def forge_vms(tmp_path):
    root = Path(__file__).resolve().parents[2]
    shutil.copy2(root / 'forge', tmp_path / 'forge')
    shutil.copytree(root / 'development/playbooks/vms', tmp_path / 'development/playbooks/vms')
    inventory = tmp_path / 'inventories'
    inventory.mkdir()
    (inventory / 'localhost').write_text(
        f'localhost ansible_connection=local ansible_python_interpreter={sys.executable}\n'
    )
    scripts = tmp_path / 'development/scripts'
    scripts.mkdir()
    inventory_script = scripts / 'vagrant.py'
    inventory_script.write_text('#!/bin/sh\nprintf "all:\\n  hosts: {}\\n"\n')
    inventory_script.chmod(0o755)

    # Record the Vagrant commands without allocating or changing any VMs.
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    vagrant = binaries / 'vagrant'
    vagrant.write_text(
        f'#!{sys.executable}\n'
        'import json, os, sys\n'
        'with open(os.environ["VAGRANT_TEST_LOG"], "a") as log:\n'
        '    log.write(json.dumps([sys.argv[1:], os.environ.get("FOREMANCTL_SYNCED_FOLDER")]) + "\\n")\n'
    )
    vagrant.chmod(0o755)
    config = tmp_path / 'ansible.cfg'
    config.write_text('[defaults]\nretry_files_enabled = false\n')
    log = tmp_path / 'vagrant.jsonl'
    env = os.environ.copy()
    env.pop('FOREMANCTL_SYNCED_FOLDER', None)
    env.update({
        'PATH': f'{binaries}{os.pathsep}{env["PATH"]}',
        'ANSIBLE_CONFIG': str(config),
        'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible-local'),
        'ANSIBLE_REMOTE_TEMP': str(tmp_path / 'ansible-remote'),
        'VAGRANT_TEST_LOG': str(log),
    })
    return tmp_path, env, log


@pytest.mark.parametrize(('inherited', 'option', 'expected'), [
    (None, None, 'enabled'),
    ('', None, 'enabled'),
    ('disabled', None, 'disabled'),
    (None, 'disabled', 'disabled'),
    ('disabled', 'enabled', 'enabled'),
    ('enabled', 'disabled', 'disabled'),
])
def test_vms_shared_folder_setting_reaches_up_and_provision(forge_vms, inherited, option, expected):
    root, env, log = forge_vms
    if inherited is not None:
        env['FOREMANCTL_SYNCED_FOLDER'] = inherited
    command = ['./forge', 'vms', 'start', '--vms', 'quadlet client']
    if option is not None:
        command += ['--synced-folder', option]
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert [json.loads(line) for line in log.read_text().splitlines()] == [
        [['up', 'quadlet', 'client'], expected],
        [['provision', 'quadlet', 'client'], expected],
    ]
    assert (root / 'inventories/local_vagrant').exists()


def test_vms_rejects_invalid_shared_folder_option(forge_vms):
    root, env, log = forge_vms
    result = subprocess.run(
        ['./forge', 'vms', 'start', '--synced-folder', 'invalid'],
        cwd=root, env=env, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert 'invalid choice' in result.stderr
    assert not log.exists()
