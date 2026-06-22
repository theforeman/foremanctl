import re

import pytest
import yaml

BACKUP_DIR = "/tmp/foremanctl-backup-test"


@pytest.fixture(scope="module")
def backup_result(server):
    import os
    import subprocess

    server.run(f"rm -rf {BACKUP_DIR}")

    result = server.run(f"mkdir -p {BACKUP_DIR}")
    assert result.rc == 0, f"Failed to create backup directory on VM: {result.stderr}"

    foremanctl_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_cmd = [
        './foremanctl',
        'backup',
        BACKUP_DIR
    ]

    result = subprocess.run(
        backup_cmd,
        cwd=foremanctl_dir,
        capture_output=True,
        text=True
    )

    find_result = server.run(f"ls -1 {BACKUP_DIR}")
    assert find_result.rc == 0, f"Backup directory should exist on VM. ls output: {find_result.stderr}"

    backup_dirs = [d for d in find_result.stdout.split('\n') if d.startswith('foreman-backup-')]
    assert len(backup_dirs) > 0, \
        f"Should have created a timestamped backup directory. Command rc={result.returncode}, stdout={result.stdout}, stderr={result.stderr}, ls output={find_result.stdout}"

    backup_dir_name = backup_dirs[0]
    full_backup_path = f"{BACKUP_DIR}/{backup_dir_name}"

    return {
        'result': result,
        'backup_dir': full_backup_path,
        'backup_dir_name': backup_dir_name,
    }


def test_foreman_service_running(server):
    """Test that Foreman is deployed and running before backup tests"""
    foreman = server.service("foreman.target")
    assert foreman.is_running, "Foreman must be running to test backup"


def test_postgresql_running(server, database_mode):
    """Test that PostgreSQL is running before backup tests"""
    if database_mode == 'external':
        pytest.skip("PostgreSQL service not managed by foremanctl in external database mode")
    postgresql = server.service("postgresql")
    assert postgresql.is_running, "PostgreSQL must be running to test backup"


def test_backup_directory_created(backup_result):
    """Test that backup creates a timestamped directory"""
    backup_dir_name = backup_result['backup_dir_name']

    timestamp_pattern = r'foreman-backup-\d{8}T\d{6}'
    assert re.match(timestamp_pattern, backup_dir_name), \
        f"Backup directory should match pattern foreman-backup-YYYYMMDDTHHMMSS, got: {backup_dir_name}"


def test_backup_command_succeeded(backup_result):
    """Test that backup command completed successfully"""
    result = backup_result['result']
    assert result.returncode == 0, f"Backup command should succeed, got rc={result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"


def test_database_dumps_created(server, backup_result):
    """Test that all database dump files are created"""
    backup_dir = backup_result['backup_dir']

    expected_dumps = ['foreman.dump', 'candlepin.dump', 'pulp.dump']

    for dump_file in expected_dumps:
        dump_path = f"{backup_dir}/{dump_file}"
        file_check = server.file(dump_path)
        assert file_check.exists, f"Database dump {dump_file} should exist at {dump_path}"
        assert file_check.is_file, f"{dump_file} should be a file"
        assert file_check.size > 0, f"{dump_file} should not be empty"


@pytest.mark.feature("iop")
def test_iop_database_dumps_created(server, backup_result):
    backup_dir = backup_result['backup_dir']

    expected_iop_dumps = [
        'iop_advisor.dump',
        'iop_inventory.dump',
        'iop_remediation.dump',
        'iop_vmaas.dump',
        'iop_vulnerability.dump',
    ]

    for dump_file in expected_iop_dumps:
        dump_path = f"{backup_dir}/{dump_file}"
        file_check = server.file(dump_path)
        assert file_check.exists, f"IOP database dump {dump_file} should exist at {dump_path}"
        assert file_check.is_file, f"{dump_file} should be a file"
        assert file_check.size > 0, f"{dump_file} should not be empty"


def test_database_dumps_valid_format(server, backup_result):
    """Test that database dumps are in valid pg_dump custom format"""
    backup_dir = backup_result['backup_dir']

    for dump_file in ['foreman.dump', 'candlepin.dump', 'pulp.dump']:
        dump_path = f"{backup_dir}/{dump_file}"

        result = server.run(f"head -c 5 {dump_path}")
        assert result.rc == 0
        assert result.stdout.startswith('PGDMP'), \
            f"{dump_file} should be a valid pg_dump custom format file (should start with PGDMP)"


@pytest.mark.feature("iop")
def test_iop_database_dumps_valid_format(server, backup_result):
    backup_dir = backup_result['backup_dir']

    iop_dumps = [
        'iop_advisor.dump',
        'iop_inventory.dump',
        'iop_remediation.dump',
        'iop_vmaas.dump',
        'iop_vulnerability.dump',
    ]

    for dump_file in iop_dumps:
        dump_path = f"{backup_dir}/{dump_file}"
        result = server.run(f"head -c 5 {dump_path}")
        assert result.rc == 0
        assert result.stdout.startswith('PGDMP'), \
            f"{dump_file} should be a valid pg_dump custom format file (should start with PGDMP)"


def test_foremanctl_state_archived(server, backup_result):
    """
    Test that foremanctl state directory is archived.

    NOTE: This test is conditional because foremanctl-state.tar.gz is only
    created in production deployments where Foreman and foremanctl run on
    the same machine (ansible_connection=local).

    In VM-based development and CI environments:
    - foremanctl runs on the HOST
    - Foreman runs on a separate VM
    - obsah_state_path points to the host's .var/lib/foremanctl/
    - The backup playbook runs on the VM where this path doesn't exist
    - Therefore, foremanctl-state.tar.gz is NOT created

    This is expected and not a bug. The backup feature is designed for
    production deployments where everything runs on the same server.
    """
    backup_dir = backup_result['backup_dir']
    state_archive = f"{backup_dir}/foremanctl-state.tar.gz"

    file_check = server.file(state_archive)

    if file_check.exists:
        # Production deployment - verify the archive
        assert file_check.is_file, "foremanctl-state.tar.gz should be a file"
        assert file_check.size > 0, "foremanctl-state.tar.gz should not be empty"

        result = server.run(f"tar -tzf {state_archive} | head -5")
        assert result.rc == 0, "foremanctl-state.tar.gz should be a valid tar.gz archive"
    else:
        pytest.skip(
            "foremanctl-state.tar.gz not created in VM-based testing. "
            "This is expected - the state directory exists on the host, "
            "but the backup playbook runs on the VM. "
            "In production (ansible_connection=local), this file is created."
        )


def test_pulp_content_archived(server, backup_result):
    backup_dir = backup_result['backup_dir']
    pulp_archive = f"{backup_dir}/pulp-content.tar.gz"

    file_check = server.file(pulp_archive)
    assert file_check.exists, "pulp-content.tar.gz should exist"
    assert file_check.is_file, "pulp-content.tar.gz should be a file"
    assert file_check.size > 0, "pulp-content.tar.gz should not be empty"

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


def test_metadata_file_created(server, backup_result):
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    file_check = server.file(metadata_file)
    assert file_check.exists, "metadata.yml should exist"
    assert file_check.is_file, "metadata.yml should be a file"
    assert file_check.size > 0, "metadata.yml should not be empty"


def test_metadata_structure(server, backup_result):
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    result = server.run(f"cat {metadata_file}")
    assert result.rc == 0, "Should be able to read metadata.yml"

    metadata = yaml.safe_load(result.stdout)

    required_fields = ['hostname', 'os_version', 'type', 'timestamp', 'databases', 'database_mode']
    for field in required_fields:
        assert field in metadata, f"Metadata should contain '{field}' field"

    assert metadata['type'] == 'offline', "Backup type should be 'offline'"
    assert metadata['incremental'] is False, "Backup should not be incremental"
    assert metadata['database_mode'] in ['internal', 'external'], "Database mode should be 'internal' or 'external'"

    # Core databases should always be present
    core_databases = {'foreman', 'candlepin', 'pulp'}
    actual_databases = set(metadata['databases'])
    assert core_databases.issubset(actual_databases), \
        f"Core databases {core_databases} should be present, got {actual_databases}"

    # If IOP is enabled, check for IOP databases
    if 'enabled_features' in metadata and 'iop' in metadata['enabled_features']:
        iop_databases = {'advisor_db', 'inventory_db', 'remediations_db', 'vmaas_db', 'vulnerability_db'}
        assert iop_databases.issubset(actual_databases), \
            f"IOP databases {iop_databases} should be present when IOP is enabled, got {actual_databases}"


def test_metadata_backed_up_components(server, backup_result):
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    result = server.run(f"cat {metadata_file}")
    metadata = yaml.safe_load(result.stdout)

    assert 'backed_up_components' in metadata, "Metadata should list backed up components"

    expected_components = {'databases', 'container_images', 'foremanctl_state', 'pulp_content'}
    components_set = set(metadata['backed_up_components'])

    assert expected_components.issubset(components_set), \
        f"Backed up components should include {expected_components}, got {components_set}"


@pytest.mark.feature("iop")
def test_metadata_includes_iop_databases(server, backup_result):
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    result = server.run(f"cat {metadata_file}")
    metadata = yaml.safe_load(result.stdout)

    assert 'databases' in metadata, "Metadata should contain 'databases' field"

    expected_databases = {'foreman', 'candlepin', 'pulp'}
    expected_iop_databases = {
        'advisor_db',
        'inventory_db',
        'remediations_db',
        'vmaas_db',
        'vulnerability_db',
    }

    all_expected = expected_databases | expected_iop_databases
    actual_databases = set(metadata['databases'])

    assert all_expected == actual_databases, \
        f"With IOP enabled, databases should be {all_expected}, got {actual_databases}"


def test_metadata_timestamp_valid(server, backup_result):
    backup_dir_name = backup_result['backup_dir_name']
    backup_dir = backup_result['backup_dir']
    metadata_file = f"{backup_dir}/metadata.yml"

    dir_timestamp = backup_dir_name.replace('foreman-backup-', '')

    result = server.run(f"cat {metadata_file}")
    metadata = yaml.safe_load(result.stdout)

    assert metadata['timestamp'] == dir_timestamp, \
        "Metadata timestamp should match backup directory timestamp"


def test_services_running_after_backup(server, backup_result, database_mode):
    foreman_target = server.service("foreman.target")
    assert foreman_target.is_running, "foreman.target should be running after backup"
    key_services = [
        "redis",
        "foreman",
        "pulp-api",
        "pulp-content",
        "candlepin",
    ]

    # Only check PostgreSQL service in internal database mode
    if database_mode == 'internal':
        key_services.insert(0, "postgresql")

    for service_name in key_services:
        service = server.service(service_name)
        assert service.is_running, f"{service_name} should be running after backup"


def test_backup_files_readable(server, backup_result):
    """
    Test that all backup files have appropriate permissions.

    Note: foremanctl-state.tar.gz is only present in production deployments
    (ansible_connection=local). In VM-based testing, this file is not created.
    """
    backup_dir = backup_result['backup_dir']

    # Check directory is readable
    dir_check = server.file(backup_dir)
    assert dir_check.is_directory
    assert dir_check.mode == 0o770 or dir_check.mode == 0o40770, \
        f"Backup directory should have mode 0770, got {oct(dir_check.mode)}"

    files_to_check = [
        'metadata.yml',
        'foreman.dump',
        'candlepin.dump',
        'pulp.dump',
        'pulp-content.tar.gz',
    ]

    optional_files = [
        'foremanctl-state.tar.gz',  # Only in production (ansible_connection=local)
    ]

    for filename in files_to_check:
        file_path = f"{backup_dir}/{filename}"
        file_check = server.file(file_path)
        assert file_check.exists, f"{filename} should exist"
        assert file_check.mode & 0o400, f"{filename} should be readable by owner"

    for filename in optional_files:
        file_path = f"{backup_dir}/{filename}"
        file_check = server.file(file_path)
        if file_check.exists:
            assert file_check.mode & 0o400, f"{filename} should be readable by owner if present"
