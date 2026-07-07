import re
import subprocess

import pytest
import yaml

BACKUP_DIR = "/tmp/foremanctl-backup-test"


@pytest.fixture(scope="module")
def expected_databases(enabled_features, flavor):
    """
    Determine expected databases based on flavor and enabled features.

    Note: These names correspond to the actual database name used for
    the dump filename (e.g., 'foreman.dump'), matching the database_mapping
    in backup metadata.
    """
    databases = []

    # Katello flavor has foreman, candlepin, and pulp
    if flavor == 'katello':
        databases = ['foreman', 'candlepin', 'pulp']

    # Foreman-proxy-content flavor only has pulp
    elif flavor == 'foreman-proxy-content':
        databases = ['pulp']

    # Add IOP databases if IOP feature is enabled
    if 'iop' in enabled_features:
        databases.extend([
            'advisor_db',
            'inventory_db',
            'remediations_db',
            'vmaas_db',
            'vulnerability_db',
        ])

    return databases


@pytest.fixture(scope="module")
def backup_result(server, server_hostname):
    server.run(f"rm -rf {BACKUP_DIR}")

    result = server.run(f"mkdir -p {BACKUP_DIR}")
    assert result.rc == 0, f"Failed to create backup directory on VM: {result.stderr}"

    result = subprocess.run(
        ['./foremanctl', 'backup', BACKUP_DIR, '--target-host', server_hostname],
        capture_output=True, text=True,
    )
    returncode = result.returncode

    find_result = server.run(f"ls -1 {BACKUP_DIR}")
    assert find_result.rc == 0, f"Backup directory should exist on VM. ls output: {find_result.stderr}"

    backup_dirs = [d for d in find_result.stdout.split('\n') if d.startswith('foreman-backup-')]
    assert len(backup_dirs) > 0, \
        f"Should have created a timestamped backup directory. Command rc={returncode}, stdout={result.stdout}, stderr={result.stderr}, ls output={find_result.stdout}"

    backup_dir_name = backup_dirs[0]
    full_backup_path = f"{BACKUP_DIR}/{backup_dir_name}"

    return {
        'returncode': returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'backup_dir': full_backup_path,
        'backup_dir_name': backup_dir_name,
    }


@pytest.fixture(scope="module")
def backup_metadata(server, backup_result):
    """Load and parse the backup metadata.yml file"""
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"
    content = server.file(metadata_file).content_string
    return yaml.safe_load(content)


def test_backup_directory_created(server, backup_result):
    """Test that backup creates a timestamped directory with correct permissions"""
    backup_dir_name = backup_result['backup_dir_name']
    backup_dir = backup_result['backup_dir']

    timestamp_pattern = r'foreman-backup-\d{8}T\d{6}'
    assert re.match(timestamp_pattern, backup_dir_name), \
        f"Backup directory should match pattern foreman-backup-YYYYMMDDTHHMMSS, got: {backup_dir_name}"

    # Check directory permissions
    dir_check = server.file(backup_dir)
    assert dir_check.is_directory
    assert dir_check.mode == 0o770 or dir_check.mode == 0o40770, \
        f"Backup directory should have mode 0770, got {oct(dir_check.mode)}"


def test_backup_command_succeeded(backup_result):
    """Test that backup command completed successfully"""
    returncode = backup_result['returncode']
    stdout = backup_result['stdout']
    stderr = backup_result['stderr']
    assert returncode == 0, f"Backup command should succeed, got rc={returncode}\nstdout: {stdout}\nstderr: {stderr}"


def test_database_dumps_created(server, backup_result, expected_databases):
    """Test that all database dump files are created and valid"""
    backup_dir = backup_result['backup_dir']

    for database_name in expected_databases:
        dump_file = f"{database_name}.dump"
        dump_path = f"{backup_dir}/{dump_file}"
        file_check = server.file(dump_path)
        assert file_check.exists, f"Database dump {dump_file} should exist at {dump_path}"
        assert file_check.is_file, f"{dump_file} should be a file"
        assert file_check.size > 0, f"{dump_file} should not be empty"
        assert file_check.mode & 0o400, f"{dump_file} should be readable by owner"

        # Verify pg_dump custom format
        result = server.run(f"head -c 5 {dump_path}")
        assert result.rc == 0
        assert result.stdout.startswith('PGDMP'), \
            f"{dump_file} should be a valid pg_dump custom format file (should start with PGDMP)"


@pytest.mark.feature("iop")
def test_iop_database_dumps_created(server, backup_result):
    """Test that all IOP database dump files are created and valid"""
    backup_dir = backup_result['backup_dir']

    expected_iop_dumps = [
        'advisor_db.dump',
        'inventory_db.dump',
        'remediations_db.dump',
        'vmaas_db.dump',
        'vulnerability_db.dump',
    ]

    for dump_file in expected_iop_dumps:
        dump_path = f"{backup_dir}/{dump_file}"
        file_check = server.file(dump_path)
        assert file_check.exists, f"IOP database dump {dump_file} should exist at {dump_path}"
        assert file_check.is_file, f"{dump_file} should be a file"
        assert file_check.size > 0, f"{dump_file} should not be empty"
        assert file_check.mode & 0o400, f"{dump_file} should be readable by owner"

        # Verify pg_dump custom format
        result = server.run(f"head -c 5 {dump_path}")
        assert result.rc == 0
        assert result.stdout.startswith('PGDMP'), \
            f"{dump_file} should be a valid pg_dump custom format file (should start with PGDMP)"


def test_foremanctl_state_archived(server, backup_result):
    """
    Test that foremanctl state directory is archived.

    The backup role archives the controller's obsah_state_path to capture
    deployment state including secrets and configuration. This works for:
    - Local deployment: controller and target are the same machine
    - Quadlet deployment: controller has the state, archive transferred to target
    - Proxy deployment: similar to quadlet
    """
    backup_dir = backup_result['backup_dir']
    state_archive = f"{backup_dir}/foremanctl-state.tar.gz"

    file_check = server.file(state_archive)
    assert file_check.exists, "foremanctl-state.tar.gz should exist"
    assert file_check.is_file, "foremanctl-state.tar.gz should be a file"
    assert file_check.size > 0, "foremanctl-state.tar.gz should not be empty"
    assert file_check.mode & 0o400, "foremanctl-state.tar.gz should be readable by owner"

    result = server.run(f"tar -tzf {state_archive} | head -5")
    assert result.rc == 0, "foremanctl-state.tar.gz should be a valid tar.gz archive"


def test_foremanctl_state_archive_contents(server, backup_result):
    """Test that foremanctl state archive contains expected deployment files"""
    backup_dir = backup_result['backup_dir']
    state_archive = f"{backup_dir}/foremanctl-state.tar.gz"

    # Get archive contents
    result = server.run(f"tar -tzf {state_archive}")
    assert result.rc == 0, "Should be able to list archive contents"

    archive_contents = result.stdout
    file_list = [f for f in archive_contents.split('\n') if f and not f.endswith('/')]

    assert len(file_list) > 0, "Archive should contain at least one file"

    # Check for certificates-ca-password which should be present in all deployments
    assert 'certificates-ca-password' in archive_contents, \
        "Archive should contain certificates-ca-password (generated during deployment)"


def test_pulp_content_archived(server, backup_result):
    backup_dir = backup_result['backup_dir']
    pulp_archive = f"{backup_dir}/pulp-content.tar.gz"

    file_check = server.file(pulp_archive)
    assert file_check.exists, "pulp-content.tar.gz should exist"
    assert file_check.is_file, "pulp-content.tar.gz should be a file"
    assert file_check.size > 0, "pulp-content.tar.gz should not be empty"
    assert file_check.mode & 0o400, "pulp-content.tar.gz should be readable by owner"

    result = server.run(f"tar -tzf {pulp_archive} | head -10")
    assert result.rc == 0, "pulp-content.tar.gz should be a valid tar.gz archive"

    archive_contents = server.run(f"tar -tzf {pulp_archive}").stdout
    assert 'media' in archive_contents, "Archive should contain media directory"
    assert 'database_fields.symmetric.key' in archive_contents, "Archive should contain database encryption key"
    assert 'django_secret_key' in archive_contents, "Archive should contain django secret key"


def test_pulp_content_excludes_correct_directories(server, backup_result):
    backup_dir = backup_result['backup_dir']
    pulp_archive = f"{backup_dir}/pulp-content.tar.gz"

    archive_contents = server.run(f"tar -tzf {pulp_archive}").stdout

    assert 'media/exports' not in archive_contents, "Archive should exclude media/exports"
    assert 'media/imports' not in archive_contents, "Archive should exclude media/imports"
    assert 'media/sync_imports' not in archive_contents, "Archive should exclude media/sync_imports"


def test_metadata_file_exists(server, backup_result):
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    file_check = server.file(metadata_file)
    assert file_check.exists, "metadata.yml should exist"
    assert file_check.is_file, "metadata.yml should be a file"
    assert file_check.size > 0, "metadata.yml should not be empty"
    assert file_check.mode & 0o400, "metadata.yml should be readable by owner"


def test_metadata_structure(backup_metadata, expected_databases):
    required_fields = ['hostname', 'os_version', 'type', 'timestamp', 'databases', 'database_mode']
    for field in required_fields:
        assert field in backup_metadata, f"Metadata should contain '{field}' field"

    assert backup_metadata['type'] == 'offline', "Backup type should be 'offline'"
    assert backup_metadata['incremental'] is False, "Backup should not be incremental"
    assert backup_metadata['database_mode'] in ['internal', 'external'], "Database mode should be 'internal' or 'external'"

    # Verify expected databases are present
    expected_db_set = set(expected_databases)
    actual_databases = set(backup_metadata['databases'])
    assert expected_db_set == actual_databases, \
        f"Expected databases {expected_db_set} should match actual {actual_databases}"


def test_metadata_backed_up_components(backup_metadata):
    assert 'backed_up_components' in backup_metadata, "Metadata should list backed up components"

    expected_components = {'databases', 'container_images', 'foremanctl_state', 'pulp_content'}
    components_set = set(backup_metadata['backed_up_components'])

    assert expected_components.issubset(components_set), \
        f"Backed up components should include {expected_components}, got {components_set}"


@pytest.mark.feature("iop")
def test_metadata_includes_iop_databases(backup_metadata, expected_databases):
    assert 'databases' in backup_metadata, "Metadata should contain 'databases' field"

    # With IOP enabled, expected_databases fixture should include IOP databases
    expected_db_set = set(expected_databases)
    actual_databases = set(backup_metadata['databases'])

    # Verify IOP databases are present
    # Note: These are the 'name' values from database.yml, not the actual PostgreSQL database names
    expected_iop_databases = {
        'iop_advisor',
        'iop_inventory',
        'iop_remediation',
        'iop_vmaas',
        'iop_vulnerability',
    }
    assert expected_iop_databases.issubset(actual_databases), \
        f"With IOP enabled, databases should include {expected_iop_databases}, got {actual_databases}"

    assert expected_db_set == actual_databases, \
        f"Expected databases {expected_db_set} should match actual {actual_databases}"


def test_metadata_timestamp_valid(backup_result, backup_metadata):
    backup_dir_name = backup_result['backup_dir_name']
    dir_timestamp = backup_dir_name.replace('foreman-backup-', '')

    assert backup_metadata['timestamp'] == dir_timestamp, \
        "Metadata timestamp should match backup directory timestamp"


def test_health_check_passes_after_backup(server, backup_result):
    """Verify system is healthy after backup using foremanctl health check"""
    result = subprocess.run(['./foremanctl', 'health'], capture_output=True, text=True)
    assert result.returncode == 0, f"Health check should pass after backup. Output:\n{result.stdout}\n{result.stderr}"
