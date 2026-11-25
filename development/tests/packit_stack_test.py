import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from ansible.errors import AnsibleFilterError
from packit_stack import packit_stack_plan

ROOT = Path(__file__).resolve().parents[2]
FOREMAN = 'https://github.com/theforeman/foreman/pull/100'
FOREMAN_PLUGIN = 'https://github.com/theforeman/foreman_ansible/pull/200'
PROXY = 'https://github.com/theforeman/smart-proxy/pull/300'
PROXY_PLUGIN = 'https://github.com/example/smart_proxy_ansible/pull/400'


@pytest.fixture(autouse=True)
def isolated_parameters(monkeypatch, tmp_path):
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))


def test_server_plan_groups_components_and_preserves_quoted_arguments():
    plan = packit_stack_plan('server', [FOREMAN, FOREMAN_PLUGIN, FOREMAN], [PROXY, PROXY_PLUGIN],
                             '--initial-organization "My organization" --tuning development')
    assert plan == {
        'target': 'quadlet',
        'command': 'deploy',
        'arguments': ['--flavor', 'katello', '--initial-organization', 'My organization', '--tuning', 'development',
                      '--add-feature', 'foreman-proxy'],
        'projects': {
            'foreman': ['theforeman-foreman-100', 'theforeman-foreman_ansible-200'],
            'foreman-proxy': ['theforeman-smart-proxy-300', 'example-smart_proxy_ansible-400'],
        },
    }


def test_standalone_proxy_plan_preserves_auth_bundle_arguments():
    plan = packit_stack_plan('proxy', [], [PROXY, PROXY_PLUGIN],
                             '--auth-bundle "/tmp/my bundle.tar.gz" --foreman-fqdn foreman.example.com')
    assert plan['target'] == 'proxy'
    assert plan['command'] == 'deploy-proxy'
    assert plan['arguments'] == [
        '--flavor', 'foreman-proxy-content',
        '--auth-bundle', '/tmp/my bundle.tar.gz', '--foreman-fqdn', 'foreman.example.com',
    ]
    assert list(plan['projects']) == ['foreman-proxy']


def test_deployment_reset_options_remain_available():
    plan = packit_stack_plan('server', [FOREMAN], [], '--reset-tuning')
    assert plan['arguments'] == ['--flavor', 'katello', '--reset-tuning']


def test_standalone_proxy_overrides_persisted_server_flavor(tmp_path):
    (tmp_path / 'parameters.yaml').write_text('flavor: katello\n')
    plan = packit_stack_plan('proxy', [], [PROXY], '')
    assert plan['arguments'][:2] == ['--flavor', 'foreman-proxy-content']


@pytest.mark.parametrize(('deployment', 'foreman', 'proxy', 'arguments'), [
    ('unknown', [FOREMAN], [], ''),
    ('server', [], [], ''),
    ('proxy', [FOREMAN], [PROXY], ''),
    ('server', ['https://example.com/foreman/pull/100'], [], ''),
    ('server', [FOREMAN], [], '--unknown-deploy-option'),
    ('server', [FOREMAN], [], '--tuning "unclosed quote'),
    ('server', [FOREMAN], [], '--air-gapped'),
    ('proxy', [], [PROXY], '--initial-admin-password changeme'),
])
def test_invalid_input_is_rejected_before_deployment(deployment, foreman, proxy, arguments):
    with pytest.raises(AnsibleFilterError):
        packit_stack_plan(deployment, foreman, proxy, arguments)


@pytest.mark.parametrize(('deployment', 'build_fails', 'deploy_fails', 'target_exists'), [
    ('server', False, False, True), ('proxy', False, False, True),
    ('server', True, False, True), ('proxy', False, True, True),
    ('server', False, False, False), ('proxy', False, False, False),
])
def test_workflow_builds_before_deployment_and_stops_on_failure(
    tmp_path, deployment, build_fails, deploy_fails, target_exists,
):
    """Stub image building and service management; run the real orchestration plays locally."""
    role = tmp_path / 'roles/deploy_packit/tasks'
    role.mkdir(parents=True)
    (role / 'main.yaml').write_text(yaml.safe_dump([
        {
            'name': 'Verify fresh component build',
            'ansible.builtin.assert': {
                'that': ['deploy_packit_pull', 'not deploy_packit_show_next_step',
                         'deploy_packit_projects | length == 1'],
            },
        },
        {
            'name': 'Record component build',
            'ansible.builtin.debug': {'msg': 'BUILD {{ deploy_packit_component }}'},
        },
        {
            'name': 'Simulate a failed build',
            'ansible.builtin.fail': {'msg': 'Image build failed'},
            'when': 'stub_build_fails and deploy_packit_component == "foreman-proxy"',
        },
    ]))
    inventory = tmp_path / 'inventory.yaml'
    inventory.write_text(yaml.safe_dump({'all': {
        'hosts': {host: {'ansible_connection': 'local'}
                  for host in (('localhost', 'quadlet', 'proxy') if target_exists else ('localhost',))},
        'vars': {'ansible_python_interpreter': sys.executable},
    }}))
    variables = {
        'deploy_packit_stack_deployment': deployment,
        'deploy_packit_stack_foreman_urls': [FOREMAN] if deployment == 'server' else [],
        'deploy_packit_stack_proxy_urls': [PROXY],
        # printf records the chosen subcommand without invoking a real deployment.
        'deploy_packit_stack_foremanctl': '/usr/bin/false' if deploy_fails else '/usr/bin/printf',
        'stub_build_fails': build_fails,
    }
    result = subprocess.run([
        'ansible-playbook', '-i', str(inventory),
        str(ROOT / 'development/playbooks/deploy-packit-stack/deploy-packit-stack.yaml'),
        '--skip-tags', 'packit-stop-services', '-e', json.dumps(variables),
    ], env=os.environ | {
        'ANSIBLE_ROLES_PATH': str(tmp_path / 'roles'),
        'ANSIBLE_FILTER_PLUGINS': str(ROOT / 'development/filter_plugins'),
        'ANSIBLE_STDOUT_CALLBACK': 'default',
        'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible'),
    }, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert (result.returncode != 0) == (build_fails or deploy_fails or not target_exists), output
    if build_fails or not target_exists:
        assert 'Deploy using the locally built images' not in output
        if not target_exists:
            assert 'Configure the ' in output
            assert 'BUILD ' not in output
    else:
        assert 'BUILD foreman-proxy' in output
        if deployment == 'server':
            assert output.index('BUILD foreman') < output.index('BUILD foreman-proxy')
        assert output.index('BUILD foreman-proxy') < output.index('Deploy using the locally built images')
