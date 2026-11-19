"""Check Packit component selection locally without building images or using VMs."""

import os
import shutil
import subprocess
from pathlib import Path

import obsah
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


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
def test_component_image_selection(monkeypatch, tmp_path, cli_args, image_vars, repository, base_image, target_image):
    if not shutil.which('ansible-playbook'):
        pytest.skip('ansible-playbook is required')
    monkeypatch.setenv('OBSAH_DATA', str(ROOT / 'development'))
    monkeypatch.setenv('OBSAH_STATE', str(tmp_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'false')
    parser = obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])
    args = parser.parse_args(['deploy-packit'] + cli_args)
    variables = yaml.safe_load((ROOT / 'development/roles/deploy_packit/defaults/main.yaml').read_text())
    variables.update(yaml.safe_load((ROOT / 'src/vars/images.yml').read_text()))
    variables.update(image_vars)
    variables.update({key: value for key, value in vars(args).items()
                      if key.startswith('deploy_packit_') and value is not None})
    variables['expected_repository'] = repository
    variables['expected_base_image'] = base_image
    variables['expected_target_image'] = target_image
    variables['expected_organization'] = 'example' if '--pr-url' in cli_args else 'theforeman'
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
                    'deploy_packit_repo_name == expected_repository',
                    'deploy_packit_repo_org == expected_organization',
                    'deploy_packit_pr | string == "100"',
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
    assert result.returncode == 0, result.stdout + result.stderr
