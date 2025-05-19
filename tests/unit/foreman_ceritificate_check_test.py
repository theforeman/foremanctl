import pytest
import subprocess
import os
import sys
import re


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.abspath(os.path.join(TEST_DIR, '..', 'fixtures', 'foreman-certificate-check'))
SCRIPT_PATH = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'src', 'roles', 'certificate_checks', 'files', 'foreman-certificate-check'))

SCRIPT_PATH = os.path.abspath(SCRIPT_PATH)
if not os.path.exists(SCRIPT_PATH):
    pytest.fail(f"Test script not found at: {SCRIPT_PATH}")


@pytest.fixture
def command():
    return SCRIPT_PATH

@pytest.fixture
def certs_directory():
    return os.path.join(FIXTURE_DIR, 'certs')

@pytest.fixture
def ca_bundle(certs_directory):
    return os.path.join(certs_directory, 'ca-bundle.crt')

@pytest.fixture
def password_protected_key():
    return os.path.join(FIXTURE_DIR, 'key_pass.key')


def run_script(command, args=None, input=None):
    cmd = [command]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )
    return result


def test_missing_parameters(command):
    result = run_script(command)
    assert result.returncode == 1
    assert "usage:" in result.stderr
    assert "-c CERT_FILE" in result.stderr
    assert "-k KEY_FILE" in result.stderr
    assert "-b CA_BUNDLE_FILE" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("cert_type", ["rsa", "ecc"])
def test_completes_correctly_with_valid_certs(command, certs_directory, ca_bundle, cert_type):
    if cert_type == "rsa":
        key = os.path.join(certs_directory, 'foreman.example.com.key')
        cert = os.path.join(certs_directory, 'foreman.example.com.crt')
    elif cert_type == "ecc":
        key = os.path.join(certs_directory, 'foreman-ec384.example.com.key')
        cert = os.path.join(certs_directory, 'foreman-ec384.example.com.crt')
    else:
        pytest.fail(f"Unknown cert_type: {cert_type}")

    args = ['-b', ca_bundle, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Validation succeeded" in result.stdout

def test_with_password_on_key(command, ca_bundle, password_protected_key, certs_directory):
    cert = os.path.join(certs_directory, 'foreman.example.com.crt')
    args = ['-b', ca_bundle, '-k', password_protected_key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 2
    expected_error_part = f"The {password_protected_key} contains a passphrase"
    assert expected_error_part in result.stderr


def test_fails_if_purpose_not_sslserver(command, ca_bundle, certs_directory):
    key = os.path.join(certs_directory, 'invalid.key')
    cert = os.path.join(certs_directory, 'invalid.crt')
    args = ['-b', ca_bundle, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode != 0
    assert 'does not verify' in result.stderr

def test_fails_with_invalid_san(command, ca_bundle, certs_directory):
    key = os.path.join(certs_directory, 'foreman-bad-san.example.com.key')
    cert = os.path.join(certs_directory, 'foreman-bad-san.example.com.crt')
    args = ['-b', ca_bundle, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 11
    expected_error_part = 'does not have a Subject Alt Name matching the Subject CN'
    assert expected_error_part in result.stderr


def test_wildcard_certificate(command, certs_directory, ca_bundle):
    key = os.path.join(certs_directory, 'wildcard.key')
    cert = os.path.join(certs_directory, 'wildcard.crt')
    args = ['-b', ca_bundle, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 0
    assert result.stderr == ""
    assert "Validation succeeded" in result.stdout
    assert "Checking CA bundle size:" in result.stdout

def test_fails_on_shortname(command, ca_bundle, certs_directory):
    key = os.path.join(certs_directory, 'shortname.key')
    cert = os.path.join(certs_directory, 'shortname.crt')
    args = ['-b', ca_bundle, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 1
    assert f"The {os.path.basename(cert)} is using a shortname for Common Name" in result.stderr
    assert f"The {os.path.basename(cert)} is using only shortnames for Subject Alt Name" in result.stderr

def test_fails_with_bundle_containing_trust_rules(command, certs_directory):
    key = os.path.join(certs_directory, 'foreman.example.com.key')
    cert = os.path.join(certs_directory, 'foreman.example.com.crt')
    ca_bundle_with_trust = os.path.join(certs_directory, 'ca-bundle-with-trust-rules.crt')
    args = ['-b', ca_bundle_with_trust, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 10
    expected_error_part = 'The CA bundle contains 1 certificate(s) with trust rules.'
    assert expected_error_part in result.stderr

@pytest.mark.parametrize("ca_bundle_file", ["ca-sha1.crt", "ca-sha1-bundle.crt"])
def test_fails_with_sha1_ca_certificate(command, certs_directory, ca_bundle_file):
    key = os.path.join(certs_directory, 'foreman-sha1.example.com.key')
    cert = os.path.join(certs_directory, 'foreman-sha1.example.com.crt')
    ca_sha1 = os.path.join(certs_directory, ca_bundle_file)
    args = ['-b', ca_sha1, '-k', key, '-c', cert]
    result = run_script(command, args)

    assert result.returncode == 4
    expected_error_part = f"The file '{ca_sha1}' contains a certificate signed with sha1"
    assert expected_error_part in result.stderr

