# Persistent Storage for Containers

How to choose and declare persistent storage when adding a container to foremanctl.

Containers are declared with `containers.podman.podman_container` using `state: quadlet`, which
generates a `.container` quadlet unit. Storage is attached through the `volumes:` key of that task.
Choosing the wrong kind of storage is hard to correct later: it affects data retention across
upgrades, backup and restore, SELinux labelling, and whether the deployment can run rootless.

## Choosing a storage type

```
Does the container write data that must survive restart, recreation, or upgrade?
│
├─ No, the data is derived or reproducible
│    └─ No volume. Use secrets for credentials, or the container writable layer.
│
├─ Yes, and the service owns the data
│    └─ Named Podman volume            <-- default choice
│
└─ Yes, and administrators must size, mount, or manage the filesystem directly
     └─ Host bind mount, with explicitly managed ownership and an SELinux relabel
```

Use a bind mount only when the deployment must place data on a specific administrator-managed host
path or filesystem, for example a dedicated mount point, storage with external capacity management,
or a path intentionally shared with host-side tools. Named volumes can be inspected or mounted with
Podman, but they should not be used when a stable host path is part of the contract.

## Named volumes

Named volumes are the default for persistent service-owned data. Podman may initialize an eligible
new volume with ownership suitable for the container user on first mount, but this is Podman-version
and volume-state dependent. Populated or restored volumes may retain existing ownership. Check
ownership when reusing or restoring a volume, and use the `:U` mount option only when recursive
ownership adjustment is intended.

### Time-based cleanup

Named volumes can still be used for data that expires on a schedule. If cleanup needs to happen from
the host, create the volume explicitly, inspect its mountpoint, and configure the cleanup mechanism in
the same role.

`iop_ingress` follows this pattern. It stores uploaded archives in a named Podman volume and writes a
`tmpfiles.d` rule for time-based cleanup using the volume mountpoint returned by
`containers.podman.podman_volume`.

See `src/roles/iop_ingress/tasks/main.yaml`.

### Naming convention

Name persistent Podman volumes after the service and data purpose, using the same prefix as the
container:

```text
<service>-<purpose>
```

Examples:

```text
iop-core-kafka-data
iop-service-vmaas-data
iop-core-ingress-archives
```

### Where the data lives

| Mode | Location |
| --- | --- |
| Rootful | `/var/lib/containers/storage/volumes/<name>/_data` |

Do not hardcode Podman volume storage paths. Use `podman volume inspect <name>` when troubleshooting.

## Host bind mounts

Use a bind mount when an administrator needs direct control of the filesystem. The cost is that
“Direct control” means the data must live on a known host path or administrator-managed filesystem,
   for example:
   - a dedicated disk, logical volume, or externally managed mount point
   - data intentionally accessed by host-side tools
   - import/export directories supplied by the administrator
   - storage that must be managed by existing backup, monitoring, quota, or capacity tooling
ownership and SELinux labelling become your responsibility, and the host UID/GID concern described
in [Rootless considerations](#rootless-considerations) applies.

Always add an SELinux relabel suffix:

```yaml
    volumes:
      - "{{ postgresql_data_dir }}:/var/lib/pgsql/data:rw,Z"
```

| Suffix | Meaning | Use when |
| --- | --- | --- |
| `:Z` | Relabel with a private, container-specific label | One container uses the path. Default choice. |
| `:z` | Relabel with a shared label | Two or more containers share the path. |
| none | No relabel | The path is already labelled correctly. Rare. |

Do not disable SELinux labelling. `security_opt: ["label=disable"]` turns off SELinux confinement
for the whole container, not just one mount. Pulp currently does this
(`src/roles/pulp/tasks/main.yaml`) because its bind mounts include administrator-supplied import and
export paths whose labels foremanctl does not control. Treat that as a documented exception, not a
template to copy.

Directories must exist with the right ownership before the container starts. Create them in the
role, ahead of the container task.

## Bind mount ownership rules

Use bind mounts only when a stable administrator-managed host path is required. Unlike named Podman
volumes, bind mounts expose host filesystem ownership and SELinux labelling directly to the
container. The role that introduces the bind mount must prepare the path before the container starts.

Rules for bind mounts:

- Create the host directory in the role before declaring the container.
- Set ownership and permissions explicitly.
- Do not hardcode unexplained numeric UIDs or GIDs. If a numeric owner is required because the
  container process runs as that UID, document why.
- Add an SELinux relabel suffix, usually `:Z` for a private mount or `:z` for a shared mount.
- Do not disable SELinux labelling unless there is a documented exception.
- Document why a bind mount is required instead of a named Podman volume.

## Backup, restore, and upgrades

- Any new persistent volume must be considered for backup. See
  [Backup and restore](../user/backup-restore.md).
- `foremanctl backup` does not automatically discover and back up arbitrary new Podman volumes.
  When adding a persistent volume, update the backup and restore roles to include it, or explicitly
  document why the data is derived/recreatable and does not require backup.
- Data must survive a container image upgrade. Because the volume is referenced by name and is
  independent of the container, recreating the container keeps the data.
- Major version migrations mount the same storage from a different image. `postgresql` does this
  when moving between PostgreSQL major versions; see `src/roles/postgresql/tasks/upgrade.yaml`.

## Current storage usage

Current storage usage is grouped by storage type so new services can follow the closest existing pattern.

### Named Podman volumes

- Kafka uses `iop-core-kafka-data` for broker data.
- VMaaS uses `iop-service-vmaas-data` for reposcan data.
- Foreman uses `foreman-data-run` for runtime state, not primary application data.

Named volumes are the preferred pattern for persistent service-owned data.

### Host bind mounts

- PostgreSQL uses a host directory for database data.
- Pulp uses `/var/lib/pulp` for content/artifact storage.
- Valkey uses a host directory for persistent data.

Bind mounts are used when the deployment needs a stable host path or administrator-managed
filesystem. The role must create the directory, set ownership and permissions, and apply the correct
SELinux relabel option.

### PostgreSQL-backed services

- Foreman
- Candlepin
- Advisor
- Inventory
- VMaaS

These services store durable application state in PostgreSQL and generally do not need their own
persistent filesystem volume.

### Secrets/configuration only

- Foreman Proxy
- Gateway

These services primarily use secrets and generated configuration rather than persistent writable
application data.

### Asset extraction

- IoP frontend images

These images are used as a source of static assets and do not require persistent writable storage.

## Non-volume storage patterns

| Pattern | Use when | Examples |
| --- | --- | --- |
| Bind mount | PostgreSQL, Valkey, Pulp | Works, with explicitly managed ownership; does not remove the host UID/GID concern |
| PostgreSQL-backed | Durable state is in PostgreSQL | Candlepin, Foreman, Advisor, Inventory |
| Secrets only | Service only needs mounted/env credentials and config | Foreman Proxy, Gateway |
| Asset extraction | Image is used only as a source of static files | IoP frontend images |

## Known gaps

These are tracked separately. Do not treat them as patterns to copy.

**Ingress archive storage.** Ingress writes archives to `/var/tmp` inside the container
(`src/roles/iop_ingress/tasks/main.yaml`), which is lost whenever the container is recreated, such as
during redeployment or an image upgrade. This conflicts with the expected 24-hour archive
availability. Converting it to a named volume is not sufficient on its own, because the current
cleanup depends on the expiry behaviour of that path; a replacement cleanup mechanism has to land at
the same time.

## Adding a container that needs storage

1. Decide whether the data must persist. If not, do not add a volume.
2. If it must persist, use a named volume unless an administrator needs direct filesystem control.
3. Create the volume with `containers.podman.podman_volume` before the container task.
4. For a bind mount, create the directory with correct ownership first and add `:Z` or `:z`.
5. If the data expires on a schedule, provide the cleanup mechanism in the same change.
6. Check whether the new data needs to be covered by backup and restore.
7. Confirm the data survives `foremanctl deploy` being run again over the existing deployment.
