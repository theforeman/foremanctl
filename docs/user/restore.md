# Restore

The `foremanctl restore` command restores your Foreman deployment from an offline backup created with `foremanctl backup`.

## Overview

The restore process performs the following steps:

1. **Validation** - Verifies backup directory structure and required files
2. **Service shutdown** - Stops all Foreman services cleanly
3. **Database restore** - Drops and recreates databases from backup dumps
4. **Pulp content restore** - Restores Pulp media files and encryption keys
5. **State restore** - Restores OAuth keys, passwords, and configuration
6. **Deployment** - Runs deploy roles to regenerate configuration and start services
7. **Verification** - Confirms services are running and API is responding

The restore is **destructive** - all current data is replaced with data from the backup.

## Basic Usage

```bash
foremanctl restore /var/backup/foreman-backup-20260617T104115
```

This restores from the specified backup directory, which must contain:

- Database dumps (`.dump` files)
- foremanctl state archive (`foremanctl-state.tar.gz`)
- Backup metadata (`metadata.yml`)
- Optionally: Pulp content archive (`pulp-content.tar.gz`)

## Options

### Required

| Argument | Description |
|----------|-------------|
| `BACKUP_DIR` | Path to the backup directory created by `foremanctl backup`. This should be the timestamped directory (e.g., `/var/backup/foreman-backup-20260617T104115`), not the parent directory. |

### Optional

| Option | Description |
|--------|-------------|
| `--validate` | Validate the backup without performing the restore. Checks that all required files exist and the backup metadata is valid. |
| `--force` | Force restore on existing system. Required when restoring over an existing Foreman deployment to confirm you understand data will be permanently deleted. |

## Examples

### Standard Restore

```bash
foremanctl restore /var/backup/foreman-backup-20260617T104115
```

### Validate Backup

Validate a backup without restoring:

```bash
foremanctl restore /var/backup/foreman-backup-20260617T104115 --validate
```

This validates the backup and checks system requirements before proceeding.

## Prerequisites

Before restoring, ensure:

1. **Same or compatible OS version** - The restore system should match the backup system's OS version
2. **Backup compatibility** - Backup must be from the same or previous version of foremanctl (forward compatibility is not guaranteed)

## What Gets Restored

The restore process restores:
- **Databases** - All databases included in the backup (foreman, candlepin, pulp, etc.)
- **Configuration** - OAuth keys, passwords, and deployment parameters
- **Pulp Content** - Repository content files and encryption keys (if included in backup)

## Restore Process

The restore executes the following phases:

1. **Validation** - Verifies backup integrity and system requirements
2. **Restoration** - Restores databases, Pulp content, and configuration
3. **Deployment** - Runs `foremanctl deploy` to configure and start services

The process is **destructive** - all current data is replaced with backup data. If the restore fails, services are stopped and the system is left in a safe state for investigation.

## Error Handling

If the restore fails, all services are automatically stopped and the system is left in a safe state for investigation. The error message will indicate what went wrong.

**What to do next:**
1. Review the error message to identify the problem (common issues: network connectivity, external database accessibility, corrupted backup files)
2. Fix the underlying issue
3. Re-run the restore command - it's safe to retry as the restore is idempotent
4. If you need to abort the restore and return to normal operation, start services manually with: `systemctl start foreman.target`

**Important:** Once a restore begins dropping databases, the previous data cannot be recovered. Always ensure you have a valid backup before starting a restore.

## Post-Restore Verification

The restore automatically verifies that services are running and the Foreman API is responding. If verification succeeds, your system is ready to use.

Access the Foreman UI at `https://<your-hostname>` and verify your data is at the backup point-in-time state.

## Important Warnings

### Data Loss

**The restore operation is DESTRUCTIVE:**
- All current databases are dropped and recreated
- All Pulp content is replaced
- All configuration is replaced
- There is NO undo operation

**Always verify you have the correct backup before proceeding.**

### Same-Host Restore

Restoring on the same host where the backup was created replaces all current data with backup data. Useful for disaster recovery or rolling back to a previous state.

### Different-Host Restore

Restoring on a different host:
- Hostname changes may affect:
  - SSL certificates
  - Content URLs
  - External integrations
- Update `/etc/hosts` or DNS if needed
- Regenerate certificates if hostname-based

### Version Compatibility

- Backup and restore foremanctl versions should match
- Restoring to older version is not supported
- Restoring to newer version may work but is not guaranteed

### External Database Mode

For external databases:
- Ensure database server is accessible
- Database credentials must match backup
- Network connectivity is required throughout restore

### Pulp Content Size

Large Pulp content directories can take significant time to restore:
- Plan for extended restore time
- Monitor available disk space
- Consider bandwidth for network-based storage

## Troubleshooting

### Certificate Errors After Restore

If restoring to a different hostname, SSL certificates may not match. Regenerate certificates for the new hostname:

```bash
foremanctl deploy --certificates-source=default
```

### SELinux Denials

If restore fails with permission errors, check for SELinux denials:

```bash
ausearch -m avc -ts recent
```

Temporarily set SELinux to permissive for troubleshooting (not recommended for production):

```bash
setenforce 0
```

## Best Practices

Test your backups before you need them. The only way to know a backup is valid is to restore it. Set up a test system and practice the restore process periodically - you'll catch problems with backups early and build confidence in your recovery procedures.

Keep your backups secure. They contain sensitive data including database passwords, OAuth keys, and encryption keys. Store them encrypted and limit access to authorized personnel only.

Plan your restore windows carefully. Restoring large Pulp content can take time, so schedule restores during maintenance windows and communicate expected downtime to your users. Always test the restore on a non-production system first to validate timing and catch any issues.
