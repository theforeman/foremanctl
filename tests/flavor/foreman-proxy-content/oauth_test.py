import pytest

OAUTH_FILES = [
    'foreman-oauth-consumer-key',
    'foreman-oauth-consumer-secret',
]

CERTS_DIR = '/var/lib/foremanctl/certs'


@pytest.mark.parametrize("oauth_file", OAUTH_FILES)
def test_oauth_credentials_extracted_from_bundle(server, oauth_file):
    """Proxy deploy must extract OAuth credentials from the certificate bundle."""
    oauth_path = f'{CERTS_DIR}/{oauth_file}'
    oauth = server.file(oauth_path)
    assert oauth.exists, f'{oauth_path} was not extracted from the certificate bundle'
    assert oauth.size > 0
    assert oauth.mode == 0o440, f'{oauth_path} should have mode 0440, got {oct(oauth.mode)}'
