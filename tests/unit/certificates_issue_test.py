"""Generates certificates with the certificates role and inspects the result."""

import os
import shutil
import subprocess

import pytest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))
ROLES_DIR = os.path.join(REPO_DIR, 'src', 'roles')
COLLECTIONS_DIR = os.path.join(REPO_DIR, 'build', 'collections', 'foremanctl')
CHECK_SCRIPT = os.path.join(ROLES_DIR, 'certificate_checks', 'files', 'foreman-certificate-check')

HOSTNAME = 'foreman.example.com'

PLAYBOOK = """
- hosts: localhost
  gather_facts: false
  connection: local
  tasks:
    - name: Create certificate directories
      ansible.builtin.file:
        path: "{{{{ item }}}}"
        state: directory
        mode: '0755'
      loop:
        - "{directory}/certs"
        - "{directory}/private"
        - "{directory}/requests"
    - name: Issue certificates
      ansible.builtin.include_role:
        name: certificates
        tasks_from: issue
      vars:
        certificates_ca_directory: "{directory}"
        certificates_hostname: "{hostname}"
"""


def certificate_text(certificate):
    return subprocess.run(['openssl', 'x509', '-in', certificate, '-noout', '-text'],
                          text=True, capture_output=True, check=True).stdout


def key_usage(certificate):
    lines = certificate_text(certificate).splitlines()
    index = next(i for i, line in enumerate(lines) if 'X509v3 Key Usage' in line)
    return [usage.strip() for usage in lines[index + 1].split(',')]


def public_key_algorithm(certificate):
    line = next(line for line in certificate_text(certificate).splitlines() if 'Public Key Algorithm:' in line)
    return line.split('Public Key Algorithm:')[1].strip()


@pytest.fixture(scope='module')
def certificate_authority(tmp_path_factory):
    """A self-signed CA the role can sign certificates with, without needing root."""
    directory = tmp_path_factory.mktemp('certificates')
    (directory / 'certs').mkdir()
    (directory / 'private').mkdir()

    key = directory / 'private' / 'ca.key'
    certificate = directory / 'certs' / 'ca.crt'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '1',
                    '-keyout', str(key), '-out', str(certificate), '-subj', '/CN=Test CA'],
                   capture_output=True, check=True)
    return directory


def issue_certificates(directory, algorithm=None):
    ansible_playbook = shutil.which('ansible-playbook')
    if ansible_playbook is None:
        pytest.skip('ansible-playbook is not available')

    playbook = directory / 'playbook.yml'
    playbook.write_text(PLAYBOOK.format(directory=directory, hostname=HOSTNAME))

    command = [ansible_playbook, '-i', 'localhost,', str(playbook)]
    if algorithm is not None:
        command.extend(['-e', f'certificates_algorithm_type={algorithm}'])

    environment = dict(os.environ, ANSIBLE_ROLES_PATH=ROLES_DIR)
    if os.path.isdir(COLLECTIONS_DIR):
        environment['ANSIBLE_COLLECTIONS_PATH'] = COLLECTIONS_DIR

    result = subprocess.run(command, text=True, capture_output=True, env=environment)
    assert result.returncode == 0, result.stdout

    return {
        'certificate': str(directory / 'certs' / f'{HOSTNAME}.crt'),
        'key': str(directory / 'private' / f'{HOSTNAME}.key'),
        'client_certificate': str(directory / 'certs' / f'{HOSTNAME}-client.crt'),
    }


@pytest.fixture(scope='module')
def rsa_certificates(certificate_authority):
    return issue_certificates(certificate_authority)


@pytest.fixture(scope='module')
def ecc_certificates(tmp_path_factory, certificate_authority):
    directory = tmp_path_factory.mktemp('ecc')
    shutil.copytree(certificate_authority / 'certs', directory / 'certs')
    shutil.copytree(certificate_authority / 'private', directory / 'private')
    return issue_certificates(directory, 'ECC')


def test_rsa_certificates_use_an_rsa_key(rsa_certificates):
    assert public_key_algorithm(rsa_certificates['certificate']) == 'rsaEncryption'


def test_rsa_certificates_allow_key_encipherment(rsa_certificates):
    assert 'Key Encipherment' in key_usage(rsa_certificates['certificate'])


def test_ecc_certificates_use_an_ec_key(ecc_certificates):
    assert public_key_algorithm(ecc_certificates['certificate']) == 'id-ecPublicKey'


def test_ecc_certificates_only_allow_digital_signature(ecc_certificates):
    assert key_usage(ecc_certificates['certificate']) == ['Digital Signature']


def test_ecc_client_certificates_only_allow_digital_signature(ecc_certificates):
    assert key_usage(ecc_certificates['client_certificate']) == ['Digital Signature']


def test_ecc_certificates_pass_the_certificate_check(certificate_authority, ecc_certificates):
    result = subprocess.run([CHECK_SCRIPT,
                             '-c', ecc_certificates['certificate'],
                             '-k', ecc_certificates['key'],
                             '-b', str(certificate_authority / 'certs' / 'ca.crt')],
                            text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    assert 'Validation succeeded' in result.stdout
