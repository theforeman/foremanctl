import os

import pytest
import yaml


@pytest.fixture(scope="module")
def obsah_state_path():
    return os.environ.get("OBSAH_STATE", "/var/lib/foremanctl")


@pytest.fixture(scope="module")
def migrated_environment(server):
    if not server.file("/root/ssl-build.bak").exists:
        pytest.skip("Not a migrated environment")


def test_installer_directory_removed(server, migrated_environment):
    assert not server.file("/root/ssl-build").exists


def test_installer_backup_exists(server, migrated_environment):
    backup = server.file("/root/ssl-build.bak")
    assert backup.exists
    assert backup.is_directory


@pytest.mark.parametrize("subdir", ["certs", "private", "requests"])
def test_certificate_directories(server, migrated_environment, subdir):
    d = server.file(f"/var/lib/foremanctl/certs/{subdir}")
    assert d.exists
    assert d.is_directory
    assert d.mode == 0o755


def test_ca_key_unencrypted(server, migrated_environment):
    assert not server.file("/var/lib/foremanctl/certs/private/ca.pwd").exists
    key = server.file("/var/lib/foremanctl/certs/private/ca.key")
    assert key.exists
    assert key.mode == 0o600
    assert "ENCRYPTED" not in key.content_string


def test_ca_password_persisted(migrated_environment, obsah_state_path):
    password_file = os.path.join(obsah_state_path, "certificates-ca-password")
    assert os.path.exists(password_file)
    assert oct(os.stat(password_file).st_mode & 0o777) == oct(0o600)
    with open(password_file) as f:
        assert len(f.read().strip()) > 0


def test_default_certs_no_custom_source(migrated_environment, obsah_state_path):
    parameters_file = os.path.join(obsah_state_path, "parameters.yaml")
    assert os.path.exists(parameters_file)
    with open(parameters_file) as f:
        params = yaml.safe_load(f)
    assert "certificates_source" not in params


def test_answers_migration_database_mode(migrated_environment, obsah_state_path):
    parameters_file = os.path.join(obsah_state_path, "parameters.yaml")
    assert os.path.exists(parameters_file)
    with open(parameters_file) as f:
        params = yaml.safe_load(f)
    assert params.get("database_mode") == "internal"


def test_answers_migration_admin_username(migrated_environment, obsah_state_path):
    parameters_file = os.path.join(obsah_state_path, "parameters.yaml")
    assert os.path.exists(parameters_file)
    with open(parameters_file) as f:
        params = yaml.safe_load(f)
    assert params.get("foreman_initial_admin_username") == "admin"
