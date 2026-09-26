import os
import subprocess
import sys
from pathlib import Path

import obsah
import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))


def _parse_deploy_proxy(monkeypatch, tmp_path, cli_args):
    monkeypatch.setenv('OBSAH_DATA', os.path.join(REPOSITORY_ROOT, 'src'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'true')
    parser = obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])
    args = parser.parse_args(['deploy-proxy'] + cli_args)
    return args, obsah.validate_constraints(args.playbook.metadata, args)


def _run_auth_validation(tmp_path, initialized=False, auth_bundle=None):
    state_path = tmp_path / 'proxy-state'
    state_path.mkdir()
    installed_flag = state_path / '.installed'
    if initialized:
        installed_flag.touch()

    variables = {'validate_proxy_auth_installed_flag': str(installed_flag)}
    if auth_bundle is not None:
        variables['auth_bundle'] = str(auth_bundle)

    playbook_path = tmp_path / 'validate-proxy-auth.yml'
    playbook_path.write_text(
        yaml.safe_dump([
            {
                'name': 'Validate proxy authentication',
                'hosts': 'localhost',
                'gather_facts': False,
                'roles': ['validate_proxy_auth'],
                'vars': variables,
            },
        ]),
        encoding='utf-8',
    )
    environment = os.environ | {
        'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible-tmp'),
        'ANSIBLE_ROLES_PATH': os.path.join(REPOSITORY_ROOT, 'src', 'roles'),
        'ANSIBLE_STDOUT_CALLBACK': 'default',
    }
    ansible_playbook = Path(sys.executable).with_name('ansible-playbook')
    command = [
        str(ansible_playbook),
        '--inventory', 'localhost,',
        '--connection', 'local',
        str(playbook_path),
    ]
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_deploy_proxy_requires_foreman_fqdn(monkeypatch, tmp_path):
    _args, errors = _parse_deploy_proxy(monkeypatch, tmp_path, [])

    assert errors == ["one of ['--foreman-fqdn'] is required"]


def test_deploy_proxy_rejects_auth_bundle_without_foreman_fqdn(monkeypatch, tmp_path):
    _args, errors = _parse_deploy_proxy(
        monkeypatch,
        tmp_path,
        ['--auth-bundle', '/tmp/proxy.tar.gz'],
    )

    assert errors == ["one of ['--foreman-fqdn'] is required"]


def test_deploy_proxy_accepts_foreman_fqdn_without_auth_bundle(monkeypatch, tmp_path):
    _args, errors = _parse_deploy_proxy(
        monkeypatch,
        tmp_path,
        ['--foreman-fqdn', 'foreman.example.com'],
    )

    assert errors == []


def test_deploy_proxy_accepts_persisted_foreman_fqdn(monkeypatch, tmp_path):
    (tmp_path / 'parameters.yaml').write_text(
        'foreman_name: foreman.example.com\n',
        encoding='utf-8',
    )

    _args, errors = _parse_deploy_proxy(monkeypatch, tmp_path, [])

    assert errors == []


def test_initial_proxy_requires_auth_bundle(tmp_path):
    result = _run_auth_validation(tmp_path)

    assert result.returncode != 0
    assert 'An auth bundle is required because this proxy has not been initialized.' in result.stdout


def test_initialized_proxy_does_not_require_auth_bundle(tmp_path):
    result = _run_auth_validation(tmp_path, initialized=True)

    assert result.returncode == 0, result.stdout + result.stderr


def test_nonexistent_auth_bundle_fails_early(tmp_path):
    bundle_path = tmp_path / 'missing.tar.gz'

    result = _run_auth_validation(tmp_path, auth_bundle=bundle_path)

    assert result.returncode != 0
    assert f'Path to auth bundle file not found: {bundle_path}' in result.stdout


def test_existing_auth_bundle_initializes_proxy(tmp_path):
    bundle_path = tmp_path / 'proxy.tar.gz'
    bundle_path.write_text('test', encoding='utf-8')

    result = _run_auth_validation(tmp_path, auth_bundle=bundle_path)

    assert result.returncode == 0, result.stdout + result.stderr
