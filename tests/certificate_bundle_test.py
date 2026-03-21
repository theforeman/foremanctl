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
def tarball_members(server):
    result = server.run(f'tar tzf {TARBALL}')
    assert result.succeeded, f'Tarball {TARBALL} not found. Run foremanctl certificate-bundle {HOSTNAME} before tests.'
    return result.stdout.strip().splitlines()


def test_tarball_created(server):
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


def test_server_certs_are_identical(server):
    apache = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-apache.crt')
    proxy = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy.crt')
    assert apache.stdout == proxy.stdout


def test_client_certs_are_identical(server):
    proxy_client = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-foreman-proxy-client.crt')
    puppet_client = server.run(f'tar xzf {TARBALL} -O ssl-build/{HOSTNAME}/{HOSTNAME}-puppet-client.crt')
    assert proxy_client.stdout == puppet_client.stdout


def test_ca_certs_are_identical(server):
    server_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-server-ca.crt')
    default_ca = server.run(f'tar xzf {TARBALL} -O ssl-build/katello-default-ca.crt')
    assert server_ca.stdout == default_ca.stdout
