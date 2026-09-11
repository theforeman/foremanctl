import json
import os

import obsah
import pytest
import yaml
from obsah import generate_ansible_args

TRUSTED_PROXIES_KEY = ':trusted_proxies'


@pytest.fixture(scope="module")
def foreman_settings_yaml(server):
    result = server.check_output(
        "podman secret inspect foreman-settings-yaml "
        "--format '{{.SecretData}}' --showsecret"
    )
    return yaml.safe_load(result)


@pytest.fixture
def obsah_env(monkeypatch, tmp_path):
    root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    monkeypatch.setenv('OBSAH_DATA', os.path.join(root, 'src'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_INVENTORY', os.path.join(root, 'inventories'))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'true')
    return tmp_path


def _parse_deploy(cli_args):
    parser = obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])
    args = parser.parse_args(['deploy'] + cli_args)
    if obsah.ApplicationConfig.persist_params():
        args = obsah.reset_args(obsah.ApplicationConfig, args.playbook.metadata, args)
    return args, parser


def test_foreman_trusted_proxies_append_unique(obsah_env):
    args, _parser = _parse_deploy(
        [
            '--foreman-trusted-proxy-add', '10.10.10.20',
            '--foreman-trusted-proxy-add', '10.10.10.30',
            '--foreman-trusted-proxy-add', '10.10.10.20',
        ],
    )
    assert args.foreman_trusted_proxies == ['10.10.10.20', '10.10.10.30']


def test_foreman_trusted_proxies_accepts_cidr(obsah_env):
    args, _parser = _parse_deploy(['--foreman-trusted-proxy-add', '192.168.1.1/24'])
    assert args.foreman_trusted_proxies == ['192.168.1.1/24']


@pytest.mark.parametrize('invalid', ['not-an-ip', 'capsule.example.com', '999.999.1.1'])
def test_foreman_trusted_proxies_rejects_invalid_ip(obsah_env, invalid):
    parser = obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])
    with pytest.raises(SystemExit):
        parser.parse_args(['deploy', '--foreman-trusted-proxy-add', invalid])


def test_remove_foreman_trusted_proxies(obsah_env):
    parameters_file = obsah_env / 'parameters.yaml'
    parameters_file.write_text(
        yaml.safe_dump({'foreman_trusted_proxies': ['10.10.10.20', '10.10.10.30']}),
        encoding='utf-8',
    )

    args, parser = _parse_deploy(
        ['--foreman-trusted-proxy-remove', '10.10.10.20'],
    )

    expected = ['10.10.10.30']
    inventory_path = obsah.ApplicationConfig.inventory_path()
    ansible_args = generate_ansible_args(inventory_path, args, parser.obsah_arguments)
    extra_vars = json.loads(ansible_args[-1])
    assert args.foreman_trusted_proxies == extra_vars['foreman_trusted_proxies'] == expected


def test_foreman_settings_trusted_proxies_include_localhost(foreman_settings_yaml):
    trusted = foreman_settings_yaml[TRUSTED_PROXIES_KEY]
    assert all(entry in trusted for entry in ('127.0.0.0/8', '::1'))


def test_foreman_settings_trusted_proxies_include_configured_entries(
    foreman_settings_yaml, obsah_params,
):
    configured = obsah_params.get('foreman_trusted_proxies') or []
    trusted = foreman_settings_yaml[TRUSTED_PROXIES_KEY]
    assert all(entry in trusted for entry in configured)
