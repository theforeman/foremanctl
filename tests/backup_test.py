import re

import pytest
import yaml

BACKUP_DIR = "/tmp/foremanctl-backup-test"


@pytest.fixture(scope="module")
def backup_result(server):
    server.run(f"rm -rf {BACKUP_DIR}")

    result = server.run(f"mkdir -p {BACKUP_DIR}")
    assert result.rc == 0, f"Failed to create backup directory on VM: {result.stderr}"

    result = server.run(f"./foremanctl backup {BACKUP_DIR}")

    find_result = server.run(f"ls -1 {BACKUP_DIR}")
    assert find_result.rc == 0, f"Backup directory should exist on VM. ls output: {find_result.stderr}"

    backup_dirs = [d for d in find_result.stdout.split('\n') if d.startswith('foreman-backup-')]
    assert len(backup_dirs) > 0, \
        f"Should have created a timestamped backup directory. Command rc={result.rc}, stdout={result.stdout}, stderr={result.stderr}, ls output={find_result.stdout}"

    backup_dir_name = backup_dirs[0]
    full_backup_path = f"{BACKUP_DIR}/{backup_dir_name}"

    return {
        'result': result,
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
    result = backup_result['result']
    assert result.rc == 0, f"Backup command should succeed, got rc={result.rc}\nstdout: {result.stdout}\nstderr: {result.stderr}"


def test_database_dumps_created(server, backup_result):
    """Test that all database dump files are created and valid"""
    backup_dir = backup_result['backup_dir']

    expected_dumps = ['foreman.dump', 'candlepin.dump', 'pulp.dump']

    for dump_file in expected_dumps:
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
        assert file_check.mode & 0o400, f"{dump_file} should be readable by owner"

        # Verify pg_dump custom format
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
        assert file_check.mode & 0o400, "foremanctl-state.tar.gz should be readable by owner"

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


def test_metadata_structure(backup_metadata):
    required_fields = ['hostname', 'os_version', 'type', 'timestamp', 'databases', 'database_mode']
    for field in required_fields:
        assert field in backup_metadata, f"Metadata should contain '{field}' field"

    assert backup_metadata['type'] == 'offline', "Backup type should be 'offline'"
    assert backup_metadata['incremental'] is False, "Backup should not be incremental"
    assert backup_metadata['database_mode'] in ['internal', 'external'], "Database mode should be 'internal' or 'external'"

    # Core databases should always be present
    core_databases = {'foreman', 'candlepin', 'pulp'}
    actual_databases = set(backup_metadata['databases'])
    assert core_databases.issubset(actual_databases), \
        f"Core databases {core_databases} should be present, got {actual_databases}"


def test_metadata_backed_up_components(backup_metadata):
    assert 'backed_up_components' in backup_metadata, "Metadata should list backed up components"

    expected_components = {'databases', 'container_images', 'foremanctl_state', 'pulp_content'}
    components_set = set(backup_metadata['backed_up_components'])

    assert expected_components.issubset(components_set), \
        f"Backed up components should include {expected_components}, got {components_set}"


@pytest.mark.feature("iop")
def test_metadata_includes_iop_databases(backup_metadata):
    assert 'databases' in backup_metadata, "Metadata should contain 'databases' field"

    expected_databases = {'foreman', 'candlepin', 'pulp'}
    expected_iop_databases = {
        'advisor_db',
        'inventory_db',
        'remediations_db',
        'vmaas_db',
        'vulnerability_db',
    }

    all_expected = expected_databases | expected_iop_databases
    actual_databases = set(backup_metadata['databases'])

    assert all_expected == actual_databases, \
        f"With IOP enabled, databases should be {all_expected}, got {actual_databases}"


def test_metadata_timestamp_valid(backup_result, backup_metadata):
    backup_dir_name = backup_result['backup_dir_name']
    dir_timestamp = backup_dir_name.replace('foreman-backup-', '')

    assert backup_metadata['timestamp'] == dir_timestamp, \
        "Metadata timestamp should match backup directory timestamp"


def test_health_check_passes_after_backup(server, backup_result):
    """Verify system is healthy after backup using foremanctl health check"""
    result = server.run("./foremanctl health")
    assert result.rc == 0, f"Health check should pass after backup. Output:\n{result.stdout}\n{result.stderr}"
