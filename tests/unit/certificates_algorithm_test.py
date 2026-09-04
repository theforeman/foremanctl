import json
import os
import re
import shutil
import subprocess
import sys

import pytest
import yaml

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
ROLE_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src', 'roles', 'certificates'))
DEFAULTS_FILE = os.path.join(ROLE_DIR, 'defaults', 'main.yml')
VARS_FILE = os.path.join(ROLE_DIR, 'vars', 'main.yml')

PLAYBOOK = """
- hosts: localhost
  gather_facts: false
  connection: local
  tasks:
    - name: Load role defaults
      ansible.builtin.include_vars:
        file: "{defaults}"
    - name: Load role vars
      ansible.builtin.include_vars:
        file: "{vars}"
    - name: Write resolved algorithm variables
      ansible.builtin.copy:
        content: "{{{{ {{'key_parameters': _certificates_key_parameters, 'key_usage': _certificates_key_usage}} | to_json }}}}"
        dest: "{output}"
        mode: '0644'
"""


def resolve_algorithm(tmp_path, algorithm=None):
    """Resolve the certificates role algorithm variables for the given algorithm."""
    ansible_playbook = shutil.which('ansible-playbook')
    if ansible_playbook is None:
        pytest.skip('ansible-playbook is not available')

    output = tmp_path / 'algorithm.json'
    playbook = tmp_path / 'playbook.yml'
    playbook.write_text(PLAYBOOK.format(defaults=DEFAULTS_FILE, vars=VARS_FILE, output=output))

    command = [ansible_playbook, '-i', 'localhost,', str(playbook)]
    if algorithm is not None:
        command.extend(['-e', f'certificates_algorithm_type={algorithm}'])

    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout

    return json.loads(output.read_text())


def test_default_algorithm_is_rsa():
    defaults = yaml.safe_load(open(DEFAULTS_FILE))
    assert defaults['certificates_algorithm_type'] == 'RSA'


def test_rsa_key_parameters_use_size(tmp_path):
    parameters = resolve_algorithm(tmp_path)['key_parameters']
    assert parameters['type'] == 'RSA'
    assert int(parameters['size']) == 4096
    assert 'curve' not in parameters


def test_ecc_key_parameters_use_curve(tmp_path):
    parameters = resolve_algorithm(tmp_path, 'ECC')['key_parameters']
    assert parameters['type'] == 'ECC'
    assert parameters['curve'] == 'secp384r1'
    assert 'size' not in parameters


def test_ml_dsa_is_staged_but_not_supported():
    """ML-DSA keeps its key parameters ready, but cannot be selected until key generation works."""
    variables = yaml.safe_load(open(VARS_FILE))
    assert 'ML-DSA' in variables['_certificates_algorithm_parameters']
    assert 'ML-DSA' not in variables['_certificates_supported_algorithms']


def test_ml_dsa_key_parameters_have_neither_size_nor_curve(tmp_path):
    parameters = resolve_algorithm(tmp_path, 'ML-DSA')['key_parameters']
    assert parameters['type'] == 'ML-DSA'
    assert 'size' not in parameters
    assert 'curve' not in parameters


def test_rsa_certificates_request_key_encipherment(tmp_path):
    assert resolve_algorithm(tmp_path)['key_usage'] == ['digitalSignature', 'keyEncipherment']


@pytest.mark.parametrize('algorithm', ['ECC', 'ML-DSA'])
def test_non_rsa_certificates_only_request_digital_signature(tmp_path, algorithm):
    assert resolve_algorithm(tmp_path, algorithm)['key_usage'] == ['digitalSignature']


def deploy_help():
    environment = dict(os.environ, PATH=os.pathsep.join([os.path.dirname(sys.executable), os.environ['PATH']]))
    result = subprocess.run(['./foremanctl', 'deploy', '--help'],
                            cwd=REPO_DIR, text=True, capture_output=True, env=environment)
    assert result.returncode == 0, result.stderr
    # obsah colorises its help when the terminal supports it.
    return re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)


def test_deploy_offers_every_supported_algorithm():
    variables = yaml.safe_load(open(VARS_FILE))
    choices = ','.join(variables['_certificates_supported_algorithms'])
    assert f'--certificate-algorithm {{{choices}}}' in deploy_help()


def test_deploy_does_not_offer_ml_dsa():
    assert 'ML-DSA' not in deploy_help()


def test_deploy_offers_the_ecc_curve():
    assert '--certificate-algorithm-curve' in deploy_help()
