"""Exercise the shared Packit workflow without building images or changing services."""

import json
import os
import subprocess
import sys
from pathlib import Path

import obsah
import pytest
import yaml
from obsah.constraints import validate_constraints

ROOT = Path(__file__).resolve().parents[2]
FOREMAN = 'https://github.com/theforeman/foreman/pull/100'
PROXY = 'https://github.com/theforeman/smart-proxy/pull/200'
FOREMAN_PLUGIN = 'https://github.com/theforeman/foreman_ansible/pull/300'
PROXY_PLUGIN = 'https://github.com/theforeman/smart_proxy_ansible/pull/400'


@pytest.fixture
def parser(monkeypatch, tmp_path):
    monkeypatch.setenv('OBSAH_DATA', str(ROOT / 'development'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'false')
    return obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])


@pytest.mark.parametrize(('command', 'native_options'), [
    ('deploy-packit', ['--initial-admin-password', 'test-password', '--tuning', 'development']),
    ('deploy-proxy-packit', ['--auth-bundle', '/tmp/auth bundle.tar.gz', '--foreman-fqdn', 'foreman.example.com']),
])
def test_native_deployment_options_are_inherited(parser, command, native_options):
    args = parser.parse_args([command, '--proxy-pr-url', PROXY, '--deploy'] + native_options)
    assert not validate_constraints(args.playbook.metadata, args)
    assert args.deploy_packit_deploy
    assert args.deploy_packit_proxy_urls == [PROXY]


@pytest.mark.parametrize(('command', 'deploy', 'build_fails', 'target_exists', 'running'), [
    ('deploy-packit', False, False, True, True),
    ('deploy-packit', True, False, True, True),
    ('deploy-proxy-packit', True, False, True, False),
    ('deploy-proxy-packit', True, False, True, True),
    ('deploy-packit', True, True, True, True),
    ('deploy-proxy-packit', True, False, False, False),
])
def test_shared_workflow(parser, tmp_path, command, deploy, build_fails, target_exists, running):
    proxy = command == 'deploy-proxy-packit'
    arguments = [command, '--proxy-pr-url', PROXY, '--proxy-pr-url', PROXY_PLUGIN]
    if not proxy:
        arguments += ['--foreman-pr-url', FOREMAN, '--foreman-pr-url', FOREMAN_PLUGIN,
                      '--add-feature', 'foreman-proxy']
    if deploy:
        arguments += ['--deploy']
    args = parser.parse_args(arguments)
    assert not validate_constraints(args.playbook.metadata, args)
    variables = json.loads(obsah.generate_ansible_args('unused', args, parser.obsah_arguments)[-1])
    variables['stub_build_fails'] = build_fails

    role = tmp_path / 'roles/deploy_packit/tasks'
    role.mkdir(parents=True)
    (role / 'main.yaml').write_text(yaml.safe_dump([
        {'name': 'Check builder mode', 'ansible.builtin.assert': {'that': [
            'deploy_packit_pull == (deploy_packit_deploy | default(false))',
            'deploy_packit_projects | length == 2',
        ]}},
        {'name': 'Record build', 'ansible.builtin.debug': {'msg': 'BUILD {{ deploy_packit_component }}'}},
        {'name': 'Simulate a build failure', 'ansible.builtin.fail': {'msg': 'Build failed'},
         'when': 'stub_build_fails and deploy_packit_component == "foreman-proxy"'},
    ]))
    inventory = tmp_path / 'inventory.yaml'
    hosts = ('localhost', 'quadlet', 'proxy') if target_exists else ('localhost',)
    inventory.write_text(yaml.safe_dump({'all': {
        'hosts': {name: {'ansible_connection': 'local'} for name in hosts},
        'vars': {'ansible_python_interpreter': sys.executable},
    }}))
    deployment = tmp_path / 'deployment.yaml'
    deployment.write_text(yaml.safe_dump([{
        'hosts': 'proxy' if proxy else 'quadlet', 'gather_facts': False,
        'tasks': [{'name': 'Record deployment', 'ansible.builtin.debug': {'msg': 'DEPLOY CALLED'}}],
    }]))
    # Replace only the external deployment boundary; reuse the actual composition and builder workflow.
    entry = yaml.safe_load((ROOT / f'development/playbooks/{command}/{command}.yaml').read_text())
    workflow = yaml.safe_load((ROOT / 'development/playbooks/deploy-packit/playbooks/_workflow.yaml').read_text())
    workflow[0]['tasks'][0]['ansible.builtin.import_tasks'] = str(
        ROOT / 'development/playbooks/deploy-packit/tasks/requests.yaml')
    workflow[1]['vars_files'] = [str(ROOT / 'src/vars/images.yml')]
    # Stub only stat/systemd operations; preserve the production stop conditions and ordering.
    stop = workflow[1]['tasks'][1]['block']
    stop[0] = {'name': 'Report target existence', 'ansible.builtin.set_fact': {
        'deploy_packit_existing_target': {'stat': {'exists': running}},
    }}
    stop[1].pop('ansible.builtin.systemd_service')
    stop[1]['ansible.builtin.debug'] = {'msg': 'STOP CALLED'}
    shared = tmp_path / 'prepare.yaml'
    shared.write_text(yaml.safe_dump(workflow))
    entry[0]['ansible.builtin.import_playbook'] = str(shared)
    entry[1]['ansible.builtin.import_playbook'] = str(deployment)
    playbook = tmp_path / 'workflow.yaml'
    playbook.write_text(yaml.safe_dump(entry))
    result = subprocess.run([
        'ansible-playbook', '-i', str(inventory), str(playbook),
        '-e', json.dumps(variables),
    ], env=os.environ | {
        'ANSIBLE_ROLES_PATH': str(tmp_path / 'roles'),
        'ANSIBLE_STDOUT_CALLBACK': 'default',
        'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible'),
    }, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert (result.returncode != 0) == (build_fails or not target_exists), output
    if deploy and not build_fails and target_exists:
        assert 'DEPLOY CALLED' in output
        assert output.index('BUILD foreman-proxy') < output.index('DEPLOY CALLED')
    else:
        assert 'DEPLOY CALLED' not in output
    if deploy and running and not build_fails and target_exists:
        assert output.index('BUILD foreman-proxy') < output.index('STOP CALLED') < output.index('DEPLOY CALLED')
    else:
        assert 'STOP CALLED' not in output
    if not target_exists:
        assert 'BUILD ' not in output
