import subprocess

import pytest


HOSTNAME = 'proxy.example.com'
TARBALL = f'/root/{HOSTNAME}.tar.gz'

EXPECTED_CA_FILES = [
    'ssl-build/katello-server-ca.crt',
    'ssl-build/katello-default-ca.crt',
]

EXPECTED_SERVER_FILES = [
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-apache.crt',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-apache.key',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy.crt',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy.key',
]

EXPECTED_CLIENT_FILES = [
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy-client.crt',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy-client.key',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-puppet-client.crt',
    f'ssl-build/{HOSTNAME}/{HOSTNAME}-puppet-client.key',
]


@pytest.fixture(scope="module")
def generate_custom_proxy_certs(server, certificate_source):
    if certificate_source != 'custom_server':
        yield
        return

    result = subprocess.run(
        ['./forge', 'custom-certs', '--hostname', HOSTNAME],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f'forge custom-certs failed: {result.stdout}\n{result.stderr}'
    yield


@pytest.fixture(scope="module")
def generate_bundle(server, certificate_source, generate_custom_proxy_certs):
    command = ['./foremanctl', 'certificate-bundle']
    if certificate_source == 'custom_server':
        command.extend([
            '--certificate-server-certificate', f'/root/custom-certificates/{HOSTNAME}/certs/{HOSTNAME}.crt',
            '--certificate-server-key', f'/root/custom-certificates/{HOSTNAME}/private/{HOSTNAME}.key',
            '--certificate-server-ca-certificate', '/root/custom-certificates/certs/ca.crt',
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


def test_server_certs_are_identical(server, generate_bundle):
    apache = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-apache.crt')
    assert apache.succeeded
    proxy = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy.crt')
    assert proxy.succeeded
    assert apache.stdout == proxy.stdout


def test_client_certs_are_identical(server, generate_bundle):
    proxy_client = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy-client.crt')
    assert proxy_client.succeeded
    puppet_client = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-puppet-client.crt')
    assert puppet_client.succeeded
    assert proxy_client.stdout == puppet_client.stdout


def test_proxy_certs_isolated(server, generate_bundle):
    proxy_cert = server.file(f'/root/certificates/hosts/{HOSTNAME}/certs/{HOSTNAME}.crt')
    assert proxy_cert.exists
    proxy_client_cert = server.file(f'/root/certificates/hosts/{HOSTNAME}/certs/{HOSTNAME}-client.crt')
    assert proxy_client_cert.exists


def test_proxy_certs_not_in_flat_directory(server, generate_bundle):
    flat_cert = server.file(f'/root/certificates/certs/{HOSTNAME}.crt')
    assert not flat_cert.exists


def test_ca_certs_are_identical(server, generate_bundle, default_certificates):
    server_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-server-ca.crt')
    assert server_ca.succeeded
    default_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-default-ca.crt')
    assert default_ca.succeeded
    assert server_ca.stdout == default_ca.stdout


def test_ca_certs_differ_for_custom(server, generate_bundle, custom_certificates):
    server_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-server-ca.crt')
    assert server_ca.succeeded
    default_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-default-ca.crt')
    assert default_ca.succeeded
    assert server_ca.stdout != default_ca.stdout
