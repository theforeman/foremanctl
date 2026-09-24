import os

import obsah
import pytest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))


def _parse_deploy_proxy(monkeypatch, tmp_path, cli_args):
    monkeypatch.setenv('OBSAH_DATA', os.path.join(REPOSITORY_ROOT, 'src'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'true')
    parser = obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])
    args = parser.parse_args(['deploy-proxy'] + cli_args)
    return args, obsah.validate_constraints(args.playbook.metadata, args)


def test_deploy_proxy_requires_connection_parameters(monkeypatch, tmp_path):
    _args, errors = _parse_deploy_proxy(monkeypatch, tmp_path, [])

    assert errors == ["one of ['--auth-bundle', '--foreman-fqdn'] is required"]


@pytest.mark.parametrize(
    ('cli_args', 'missing_parameter'),
    [
        (['--auth-bundle', '/tmp/proxy.tar.gz'], '--foreman-fqdn'),
        (['--foreman-fqdn', 'foreman.example.com'], '--auth-bundle'),
    ],
)
def test_deploy_proxy_requires_both_connection_parameters(
    monkeypatch, tmp_path, cli_args, missing_parameter,
):
    _args, errors = _parse_deploy_proxy(monkeypatch, tmp_path, cli_args)

    assert len(errors) == 1
    assert missing_parameter in errors[0]


def test_deploy_proxy_accepts_connection_parameters(monkeypatch, tmp_path):
    _args, errors = _parse_deploy_proxy(
        monkeypatch,
        tmp_path,
        [
            '--auth-bundle', '/tmp/proxy.tar.gz',
            '--foreman-fqdn', 'foreman.example.com',
        ],
    )

    assert errors == []
