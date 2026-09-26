import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / 'src' / 'roles' / 'systemd_target' / 'files' / 'foreman-tail'


def _write_executable(path, content):
    path.write_text(content)
    path.chmod(0o755)


def test_follows_all_direct_foreman_services(tmp_path):
    _write_executable(
        tmp_path / 'systemctl',
        '#!/bin/sh\n'
        "printf '%s\\n' 'postgresql.service foreman.service pulp-worker@2.service' "
        "'valkey.service foreman.service foreman-recurring@cleanup.timer foreman.target'\n",
    )
    _write_executable(tmp_path / 'journalctl', '#!/bin/sh\nprintf \'%s\\n\' "$@"\n')

    result = subprocess.run(
        [SCRIPT, '--since', 'today'],
        capture_output=True,
        text=True,
        env=os.environ | {'PATH': f'{tmp_path}:{os.environ["PATH"]}'},
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        '--follow',
        '--unit',
        'foreman-recurring@cleanup.service',
        '--unit',
        'foreman-recurring@cleanup.timer',
        '--unit',
        'foreman.service',
        '--unit',
        'postgresql.service',
        '--unit',
        'pulp-worker@2.service',
        '--unit',
        'valkey.service',
        '--since',
        'today',
    ]


def test_fails_when_target_has_no_services(tmp_path):
    _write_executable(tmp_path / 'systemctl', '#!/bin/sh\nexit 0\n')
    _write_executable(tmp_path / 'journalctl', '#!/bin/sh\nexit 99\n')

    result = subprocess.run(
        [SCRIPT],
        capture_output=True,
        text=True,
        env=os.environ | {'PATH': f'{tmp_path}:{os.environ["PATH"]}'},
        check=False,
    )

    assert result.returncode == 1
    assert result.stderr == 'No services found in foreman.target.\n'
