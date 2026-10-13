import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

SRC_DIR = Path(__file__).resolve().parents[2] / 'src'
URL = 'https://satellite.example.com'
PASSWORD = 'example123'


@pytest.fixture
def run_message(tmp_path):
    executable = shutil.which('ansible-playbook')
    assert executable is not None, (
        'ansible-playbook must be installed and available on PATH'
    )

    def run(*, installed=False, enabled=True, password=PASSWORD):
        marker = tmp_path / '.installed'
        if installed:
            marker.touch()

        variables = {
            'post_install_done_flag': str(marker),
            'post_install_foreman_server_url': URL,
            'post_install_foreman_initial_admin_username': 'admin',
            'post_install_foreman_initial_admin_password': password,
        }
        if enabled is not None:
            variables['post_install_message_enabled'] = enabled

        playbook = tmp_path / 'message.yaml'
        playbook.write_text(json.dumps([{
            'name': 'Test post-install message',
            'hosts': 'localhost',
            'gather_facts': False,
            'vars': variables,
            'tasks': [{
                'ansible.builtin.import_tasks': str(
                    SRC_DIR / 'roles/post_install/tasks/message.yaml'
                ),
            }],
        }]), encoding='utf-8')

        env = os.environ.copy()
        env.update({
            'ANSIBLE_CONFIG': str(SRC_DIR / 'ansible.cfg'),
            'ANSIBLE_STDOUT_CALLBACK': 'foremanctl',
            'ANSIBLE_CALLBACK_PLUGINS': str(SRC_DIR / 'callback_plugins'),
            'ANSIBLE_CALLBACK_RESULT_FORMAT': 'yaml',
            'ANSIBLE_CALLBACK_FORMAT_PRETTY': 'true',
            'ANSIBLE_NOCOLOR': '1',
            'ANSIBLE_FORCE_COLOR': '0',
            'ANSIBLE_VERBOSITY': '0',
        })

        result = subprocess.run(
            [executable, '-i', 'localhost,', '-c', 'local', str(playbook)],
            cwd=SRC_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    return run


def read_message(output):
    match = re.search(
        r'^ok: \[localhost\] =>\s*\n((?:[ \t]+[^\n]*\n|\n)+)',
        output,
        re.MULTILINE,
    )
    assert match is not None, output
    message = yaml.safe_load(match.group(1))['msg']
    assert isinstance(message, list), output
    return message


def test_first_install_displays_unquoted_credentials(run_message):
    output = run_message()

    assert read_message(output) == [
        f'You can log in at {URL}',
        f'Admin credentials admin:{PASSWORD}',
    ]

    lines = [line.strip() for line in output.splitlines()]
    assert f'- Admin credentials admin:{PASSWORD}' in lines, output


def test_existing_install_hides_credentials(run_message):
    output = run_message(installed=True)

    assert read_message(output) == [f'You can log in at {URL}', '']
    assert 'Admin credentials' not in output
    assert PASSWORD not in output


@pytest.mark.parametrize(
    'enabled',
    [False, None],
    ids=['disabled', 'undefined'],
)
def test_message_is_hidden_when_not_enabled(run_message, enabled):
    output = run_message(enabled=enabled)

    assert URL not in output
    assert 'Admin credentials' not in output
    assert PASSWORD not in output


@pytest.mark.parametrize(
    'password',
    ["pass'word:123", 'pass: word #123'],
)
def test_password_characters_are_preserved(run_message, password):
    output = run_message(password=password)

    assert read_message(output) == [
        f'You can log in at {URL}',
        f'Admin credentials admin:{password}',
    ]
