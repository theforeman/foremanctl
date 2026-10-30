import subprocess

import pytest


def test_restore_rejects_nonexistent_backup_directory(server, server_hostname, tmp_path):
    """Verify restore rejects a nonexistent backup directory."""
    backup_dir = tmp_path / 'missing-backup'
    assert not server.file(str(backup_dir)).exists

    result = subprocess.run(
        ['./foremanctl', 'restore', str(backup_dir), '--force', '--target-host', server_hostname],
        capture_output=True, text=True, timeout=300,
    )

    assert result.returncode != 0, f'Restore should fail for a missing backup:\n{result.stdout}\n{result.stderr}'
    assert f'Backup directory does not exist: {backup_dir}' in result.stdout, (
        f'Expected an error for the missing backup directory:\n{result.stdout}\n{result.stderr}'
    )


def test_restore_requires_force_on_existing_deployment(server, server_hostname, tmp_path, pytestconfig):
    """Verify restore requires --force when deployment state exists on the target."""
    state_dir = str(pytestconfig.rootpath / '.var/lib/foremanctl')
    if not server.file(state_dir).is_directory:
        pytest.skip('Requires existing deployment state on the restore target; remote restore is not supported')

    # The safety check runs before backup validation, so a full backup is unnecessary.
    backup_dir = tmp_path / 'missing-backup'
    assert not server.file(str(backup_dir)).exists
    was_running = server.service('foreman.target').is_running

    result = subprocess.run(
        ['./foremanctl', 'restore', str(backup_dir), '--target-host', server_hostname],
        capture_output=True, text=True, timeout=300,
    )

    assert result.returncode != 0, f'Restore should require --force:\n{result.stdout}\n{result.stderr}'
    assert 'An existing deployment was detected on this system.' in result.stdout, (
        f'Expected the existing-deployment safety check:\n{result.stdout}\n{result.stderr}'
    )
    assert f'foremanctl restore {backup_dir} --force' in result.stdout
    assert server.service('foreman.target').is_running == was_running, 'Rejected restore should preserve service state'
