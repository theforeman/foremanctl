import subprocess

import pytest

pytestmark = pytest.mark.feature('katello')


HOSTNAME = 'proxy.example.com'
TARBALL = f'/var/lib/foremanctl/certs/bundles/{HOSTNAME}.tar.gz'

EXPECTED_CA_FILES = [
    'certs/ca.crt',
    'certs/server-ca.crt',
    'certs/ca-bundle.crt',
]

EXPECTED_SERVER_FILES = [
    f'certs/{HOSTNAME}.crt',
    f'private/{HOSTNAME}.key',
]

EXPECTED_CLIENT_FILES = [
    f'certs/{HOSTNAME}-client.crt',
    f'private/{HOSTNAME}-client.key',
]


@pytest.fixture(scope="module")
def generate_custom_proxy_certs(server, certificate_source):
    if certificate_source != 'custom_server':
        return

    result = subprocess.run(
        ['./forge', 'custom-certs', '--hostname', HOSTNAME],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f'forge custom-certs failed: {result.stdout}\n{result.stderr}'


@pytest.fixture(scope="module")
def generate_bundle(server, certificate_source, generate_custom_proxy_certs):
    command = ['./foremanctl', 'certificate-bundle']
    if certificate_source == 'custom_server':
        command.extend([
            '--certificate-server-certificate', f'/root/custom-certificates/certs/{HOSTNAME}.crt',
            '--certificate-server-key', f'/root/custom-certificates/private/{HOSTNAME}.key',
        ])
    command.append(HOSTNAME)

    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, f'certificate-bundle failed: {result.stdout}\n{result.stderr}'


@pytest.fixture(scope="module")
def tarball_members(server, generate_bundle):
    result = server.run(f'tar tzf {TARBALL}')
    assert result.succeeded, f'Tarball {TARBALL} not found.'
    return result.stdout.strip().splitlines()


def test_tarball_created(server, generate_bundle):
    assert server.file(TARBALL).exists


@pytest.mark.parametrize("expected_file", EXPECTED_CA_FILES)
def test_tarball_contains_ca_certificate(tarball_members, expected_file):
    assert expected_file in tarball_members


@pytest.mark.parametrize("expected_file", EXPECTED_SERVER_FILES)
def test_tarball_contains_server_certificate(tarball_members, expected_file):
    assert expected_file in tarball_members


@pytest.mark.parametrize("expected_file", EXPECTED_CLIENT_FILES)
def test_tarball_contains_client_certificate(tarball_members, expected_file):
    assert expected_file in tarball_members


def test_proxy_certs_stored_in_hosts_subdirectory(server, generate_bundle):
    """Verify proxy certificates are stored in a per-host subdirectory."""
    proxy_cert = server.file(f'/var/lib/foremanctl/certs/hosts/{HOSTNAME}/certs/{HOSTNAME}.crt')
    assert proxy_cert.exists
    proxy_client_cert = server.file(f'/var/lib/foremanctl/certs/hosts/{HOSTNAME}/certs/{HOSTNAME}-client.crt')
    assert proxy_client_cert.exists


def test_server_ca_and_default_ca_identical_for_default_deployment(server, generate_bundle, default_certificates):
    """For default (non-custom) deployments, server-ca.crt and ca.crt should be identical."""
    server_ca = server.run(f'tar xzf {TARBALL} -O certs/server-ca.crt')
    assert server_ca.succeeded
    default_ca = server.run(f'tar xzf {TARBALL} -O certs/ca.crt')
    assert default_ca.succeeded
    assert server_ca.stdout == default_ca.stdout


def test_server_ca_and_default_ca_differ_for_custom_deployment(server, generate_bundle, custom_certificates):
    """For custom server cert deployments, server-ca.crt (custom) differs from ca.crt (internal)."""
    server_ca = server.run(f'tar xzf {TARBALL} -O certs/server-ca.crt')
    assert server_ca.succeeded
    default_ca = server.run(f'tar xzf {TARBALL} -O certs/ca.crt')
    assert default_ca.succeeded
    assert server_ca.stdout != default_ca.stdout
