# Service logs

Foreman services deployed by `foremanctl` are managed by systemd and write
their logs to the system journal. Use `journalctl` directly to inspect and
follow them.

## Discover services

List the services that belong to the Foreman systemd target:

```bash
systemctl list-dependencies --plain foreman.target
```

To find services that failed to start, use:

```bash
systemctl --failed
```

`foreman.target` is only a grouping unit and does not run an application
process, so it has no application logs of its own.
`journalctl -u foreman.target` can still display records associated with the
target, including systemd-generated messages about it, but it does not
aggregate messages from services listed as target dependencies.

## Inspect recent logs

Display the last 50 messages from the Foreman application:

```bash
journalctl --no-pager -n 50 -u foreman.service
```

Inspect several related services together:

```bash
journalctl --no-pager -n 200 \
  -u foreman.service \
  -u 'dynflow-sidekiq@*.service'
```

Common service units include:

- `foreman.service`
- `dynflow-sidekiq@orchestrator.service`
- `dynflow-sidekiq@worker.service`
- `dynflow-sidekiq@worker-hosts-queue.service`
- `pulp-api.service`
- `pulp-content.service`
- `pulp-worker@*.service`
- `candlepin.service`
- `httpd.service`
- `valkey.service`
- `postgresql.service`

The exact set depends on the enabled deployment features. Use
`systemctl list-dependencies` to confirm the units present on a particular
system.

## Follow logs

Follow a service in real time:

```bash
journalctl -f -u foreman.service
```

Follow Foreman and its Dynflow workers together:

```bash
journalctl -f \
  -u foreman.service \
  -u 'dynflow-sidekiq@*.service'
```

Press `Ctrl+C` to stop following the journal.

## Filter logs

Show messages from the last hour:

```bash
journalctl --since '1 hour ago' -u foreman.service
```

Show only errors and more severe messages:

```bash
journalctl -p err -u foreman.service
```

Show logs from the current boot:

```bash
journalctl -b -u foreman.service
```

Combine these options as needed. For example:

```bash
journalctl --no-pager -b -p warning --since '30 minutes ago' \
  -u foreman.service \
  -u 'dynflow-sidekiq@*.service'
```
