"""Check Packit component selection locally without building images or using VMs."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import obsah
import pytest
import yaml
from obsah.constraints import validate_constraints

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def packit_parser(monkeypatch, tmp_path):
    monkeypatch.setenv('OBSAH_DATA', str(ROOT / 'development'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'false')
    return obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])


@pytest.mark.parametrize(
    ('cli_args', 'image_vars', 'repository', 'base_image', 'target_image'),
    [
        (['--pr', '100'], {}, 'foreman',
         'quay.io/foreman/foreman:nightly', 'quay.io/foreman/foreman:nightly'),
        (['--pr', '100', '--repo-name', 'foreman_ansible'], {}, 'foreman_ansible',
         'quay.io/foreman/foreman:nightly', 'quay.io/foreman/foreman:nightly'),
        (['--component', 'foreman-proxy', '--pr', '100'], {}, 'smart-proxy',
         'quay.io/foreman/foreman-proxy:nightly', 'quay.io/foreman/foreman-proxy:nightly'),
        (['--component', 'foreman-proxy', '--pr', '100', '--repo-name', 'smart_proxy_ansible'],
         {}, 'smart_proxy_ansible',
         'quay.io/foreman/foreman-proxy:nightly', 'quay.io/foreman/foreman-proxy:nightly'),
        (['--component', 'foreman-proxy', '--pr-url', 'https://github.com/example/smart-proxy/pull/100/'],
         {}, 'smart-proxy',
         'quay.io/foreman/foreman-proxy:nightly', 'quay.io/foreman/foreman-proxy:nightly'),
        (['--component', 'foreman-proxy', '--pr', '100'],
         {'foreman_proxy_container_image': 'registry.example.com/proxy', 'foreman_proxy_container_tag': 'custom'},
         'smart-proxy', 'registry.example.com/proxy:custom', 'registry.example.com/proxy:custom'),
        (['--component', 'foreman-proxy', '--pr', '100', '--base-image', 'registry.example.com/proxy:base'],
         {}, 'smart-proxy', 'registry.example.com/proxy:base', 'quay.io/foreman/foreman-proxy:nightly'),
    ],
    ids=['foreman', 'foreman-plugin', 'proxy', 'proxy-plugin', 'proxy-url', 'configured-image', 'base-override'],
)
def test_component_image_selection(packit_parser, tmp_path, cli_args, image_vars, repository, base_image, target_image):
    organization = 'example' if '--pr-url' in cli_args else 'theforeman'
    _check_selection(packit_parser, tmp_path, cli_args, image_vars,
                     [f'{organization}-{repository}-100'], base_image, target_image)


def _check_selection(parser, tmp_path, cli_args, image_vars, projects, base_image, target_image, succeeds=True):
    if not shutil.which('ansible-playbook'):
        pytest.skip('ansible-playbook is required')
    args = parser.parse_args(['deploy-packit'] + cli_args)
    assert not validate_constraints(args.playbook.metadata, args)
    variables = yaml.safe_load((ROOT / 'development/roles/deploy_packit/defaults/main.yaml').read_text())
    variables.update(yaml.safe_load((ROOT / 'src/vars/images.yml').read_text()))
    variables.update(image_vars)
    variables.update({key: value for key, value in vars(args).items()
                      if key.startswith('deploy_packit_') and value is not None})
    variables['expected_projects'] = projects
    variables['expected_base_image'] = base_image
    variables['expected_target_image'] = target_image
    source = yaml.safe_load((ROOT / 'development/playbooks/deploy-packit/deploy-packit.yaml').read_text())[0]
    playbook = tmp_path / 'check-component.yaml'
    playbook.write_text(yaml.safe_dump([{
        'hosts': 'localhost',
        'gather_facts': False,
        'vars': variables,
        'tasks': source['pre_tasks'] + [{
            'name': 'Check selected image and repository',
            'ansible.builtin.assert': {
                'that': [
                    'deploy_packit_projects == expected_projects',
                    'deploy_packit_base_image == expected_base_image',
                    'deploy_packit_target_image == expected_target_image',
                ],
            },
        }],
    }]))
    result = subprocess.run(
        ['ansible-playbook', '-i', 'localhost,', '-c', 'local', str(playbook)],
        env=os.environ | {'ANSIBLE_LOCAL_TEMP': str(tmp_path / 'ansible')},
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) == succeeds, result.stdout + result.stderr


@pytest.mark.parametrize(('component', 'repository', 'plugin'), [
    ('foreman', 'foreman', 'foreman_ansible'),
    ('foreman-proxy', 'smart-proxy', 'smart_proxy_ansible'),
])
def test_multiple_pull_request_urls(packit_parser, tmp_path, component, repository, plugin):
    _check_selection(packit_parser, tmp_path, [
        '--component', component,
        '--pr-url', f'https://github.com/theforeman/{repository}/pull/100',
        '--pr-url', f'https://github.com/example/{plugin}/pull/200/',
        '--pr-url', f'https://github.com/theforeman/{repository}/pull/100',
    ], {}, [f'theforeman-{repository}-100', f'example-{plugin}-200'],
        f'quay.io/foreman/{component}:nightly', f'quay.io/foreman/{component}:nightly')


@pytest.mark.parametrize('extra_args', [
    ['--pr', '100'], ['--repo-org', 'example'], ['--repo-name', 'foreman_ansible'],
])
def test_pull_request_urls_reject_repository_overrides(packit_parser, extra_args):
    args = packit_parser.parse_args([
        'deploy-packit', '--pr-url', 'https://github.com/theforeman/foreman/pull/100',
    ] + extra_args)
    assert validate_constraints(args.playbook.metadata, args)


@pytest.mark.parametrize('url', [
    'https://example.com/theforeman/foreman_ansible/pull/200',
    'https://github.com/theforeman/foreman_ansible/pull/not-a-number',
    'https://github.com/invalid organization/foreman_ansible/pull/200',
])
def test_every_pull_request_url_is_validated(packit_parser, tmp_path, url):
    _check_selection(packit_parser, tmp_path, [
        '--pr-url', 'https://github.com/theforeman/foreman/pull/100', '--pr-url', url,
    ], {}, [], '', '', succeeds=False)


@pytest.mark.parametrize('failure', [None, 'enable', 'query', 'query-second', 'empty', 'empty-second', 'upgrade'])
def test_repositories_upgrade_in_one_transaction(tmp_path, failure):
    """Execute the Containerfile's RPM commands with a DNF stub that records calls."""
    log = tmp_path / 'dnf-calls.jsonl'
    dnf = tmp_path / 'dnf'
    dnf.write_text('''#!/usr/bin/env python3
import json
import os
import sys

args = sys.argv[1:]
with open(os.environ['DNF_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
failure = os.environ['DNF_FAILURE']
second_repo = '--repo=copr:copr.fedorainfracloud.org:packit:example-smart_proxy_ansible-200' in args
if (failure == 'enable' and 'enable' in args
        or failure == 'query' and 'repoquery' in args
        or failure == 'query-second' and 'repoquery' in args and second_repo
        or failure == 'upgrade' and 'upgrade' in args):
    sys.exit(1)
if 'repoquery' in args and failure != 'empty' and not (failure == 'empty-second' and second_repo):
    if second_repo:
        print('rubygem-smart_proxy_ansible-0:3.0.0-0.pr200.noarch')
    else:
        print('foreman-proxy-0:5.2.0-0.pr100.noarch')
''')
    dnf.chmod(0o755)
    containerfile = (ROOT / 'development/roles/deploy_packit/files/Containerfile').read_text()
    command = 'set -e && ' + containerfile.split('RUN set -e && ', 1)[1].split('\nUSER ', 1)[0]
    result = subprocess.run(
        ['/bin/sh', '-c', command],
        env=os.environ | {
            'PATH': f'{tmp_path}:{os.environ["PATH"]}',
            'DNF_LOG': str(log),
            'DNF_FAILURE': failure or '',
            'PACKIT_PROJECTS': 'theforeman-smart-proxy-100 example-smart_proxy_ansible-200',
        },
        capture_output=True, text=True,
    )
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    if failure:
        assert result.returncode != 0, result.stdout + result.stderr
        assert ['clean', 'all'] not in calls
        if failure != 'upgrade':
            assert not any('upgrade' in call for call in calls)
        if failure.startswith('empty'):
            project = 'example-smart_proxy_ansible-200' if failure == 'empty-second' else 'theforeman-smart-proxy-100'
            assert f'No packages found in packit/{project}' in result.stderr
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert calls[:2] == [
            ['copr', 'enable', '-y', 'packit/theforeman-smart-proxy-100', 'rhel-10-x86_64'],
            ['copr', 'enable', '-y', 'packit/example-smart_proxy_ansible-200', 'rhel-10-x86_64'],
        ]
        queries = [call for call in calls if 'repoquery' in call]
        assert len(queries) == 2
        assert '--repo=copr:copr.fedorainfracloud.org:packit:theforeman-smart-proxy-100' in queries[0]
        assert '--repo=copr:copr.fedorainfracloud.org:packit:example-smart_proxy_ansible-200' in queries[1]
        assert all('--nevra' in query for query in queries)
        assert [call for call in calls if 'upgrade' in call] == [[
            'upgrade', '-y', '--best', 'foreman-proxy-0:5.2.0-0.pr100.noarch',
            'rubygem-smart_proxy_ansible-0:3.0.0-0.pr200.noarch',
        ]]
