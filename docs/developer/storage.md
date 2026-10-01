# Persistent Storage for Containers

How to choose and declare persistent storage when adding a container to foremanctl.

Containers are declared with `containers.podman.podman_container` using `state: quadlet`, which
generates a `.container` quadlet unit. Storage is attached through the `volumes:` key of that task.
Choosing the wrong kind of storage is hard to correct later: it affects data retention across
upgrades, backup and restore, SELinux labelling, and whether the deployment can run rootless.

The guidance here follows the outcome of the IoP container runtime investigation (SAT-49504).

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

One exception is covered in [Data expiry and cleanup](#data-expiry-and-cleanup): if the data needs
time-based expiry, a named volume may not be the right answer yet.

## Named volumes

Named volumes are the default for persistent service-owned data. Podman may initialize an eligible
new volume with ownership suitable for the container user on first mount, but this is Podman-version
and volume-state dependent. Populated or restored volumes may retain existing ownership. Check
ownership when reusing or restoring a volume, and use the `:U` mount option only when recursive
ownership adjustment is intended.

Create the volume explicitly before the container that uses it, then reference it by name:

```yaml
- name: Create Kafka data volume
  containers.podman.podman_volume:
    name: iop-core-kafka-data
    state: present

- name: Deploy Kafka container
  containers.podman.podman_container:
    name: iop-core-kafka
    image: iop-kafka.image
    state: quadlet
    volumes:
      - "iop-core-kafka-data:/var/lib/kafka/data:rw"
```

See `src/roles/iop_kafka/tasks/main.yaml` and `src/roles/iop_vmaas/tasks/main.yaml` for the two
services that follow this pattern today.

Volumes are created with `containers.podman.podman_volume` rather than a `.volume` quadlet unit.
Follow that convention so volume creation stays visible in the role's task list.

Name volumes after the service and the data they hold, using the same prefix as the container:
`iop-core-kafka-data`, `iop-service-vmaas-data`.


```markdown
   ### Naming convention

   Name persistent Podman volumes after the service and data purpose:

   ```text
   <service>-<purpose>
 ```

 Examples:

 ```text
   iop-core-kafka-data
   iop-service-vmaas-data
   iop-core-ingress-archives
 ```

 ```

   Then in the checklist say:

   ```markdown
   Follow the named-volume naming convention above.
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

## Rootless considerations

foremanctl is moving toward rootless containers (SAT-45813).

A rootful container writing to a host bind mount without user-namespace remapping leaks host UID and
GID values into the data. When the same data is later accessed from a rootless container, the
container user maps to a different host UID through the `/etc/subuid` range, and the ownership no
longer matches. Named volumes avoid this because Podman owns the mapping.

If you must bind mount:

- Do not hardcode a host UID or GID. A literal `owner: "700"` is correct only for rootful operation
  and will not survive user-namespace mapping.
- Remember that `/etc/subuid` and `/etc/subgid` must have entries for the deploying user. The
  `check_subuid_subgid` role asserts this; see `src/roles/check_subuid_subgid/tasks/main.yaml`.
- Document in the role why a bind mount was necessary, so the rootless migration knows what it is
  dealing with.

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

## Current state

How each service stores persistent data

| Storage | Services | Notes |
| --- | --- | --- |
| Named volume | Kafka (`iop-core-kafka-data`), VMaaS (`iop-service-vmaas-data`) | The pattern to follow |
| Foreman | PostgreSQL; runtime named volume `foreman-data-run` | App state is in DB; runtime socket volume is not application data. |
| Pulp | PostgreSQL + bind mount `/var/lib/pulp` | Content/artifact storage requires persistent filesystem. |
| Candlepin | PostgreSQL | Config/secrets via Podman secrets. |
| Kafka | named volume `iop-core-kafka-data` | Service-owned persistent data. |
| VMaaS | PostgreSQL + named volume `iop-service-vmaas-data` | Reposcan data volume. |

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
