# TFTP integration

Foremanctl configures the Smart Proxy TFTP module to manage provisioning files
in a host directory. It creates the directory if it does not exist. When the
directory already exists, Foremanctl changes its ownership and permissions,
including those of existing contents, so the Smart Proxy can read, write, and
remove files. It keeps the existing group ownership. Foremanctl does not install
or manage the TFTP server.

The directory can be local or an NFS mount. For a separate TFTP server, make
the same files available to that server and configure it to serve them. The
When SELinux is enabled, Foremanctl labels the directory `public_content_rw_t`
and enables `container_manage_public_content` so the Smart Proxy can manage
files while the host TFTP server can read them. For an NFS directory, its
server must allow the ownership changes Foremanctl makes for Smart Proxy, and
the mount must support SELinux labels.

## Enable TFTP

Use `foremanctl deploy` for a combined Foreman and Smart Proxy deployment:

```shell
foremanctl deploy \
  --add-feature foreman-proxy \
  --add-feature tftp \
  --tftp-root /srv/provisioning/tftp \
  --tftp-servername 192.0.2.10
```

Use `foremanctl deploy-proxy` instead when deploying a standalone Smart Proxy:

```shell
foremanctl deploy-proxy \
  --add-feature tftp \
  --tftp-root /srv/provisioning/tftp \
  --tftp-servername 192.0.2.10
```
