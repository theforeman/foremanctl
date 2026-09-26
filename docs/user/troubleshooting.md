# Troubleshooting

## Follow service logs

Every deployment installs `foreman-tail`, which follows the journal for all services directly managed by `foreman.target`:

```shell
sudo foreman-tail
```

The service list is discovered from systemd, so it automatically matches the deployed flavor and enabled features. Additional arguments are passed to `journalctl`; for example, to include messages from the current day:

```shell
sudo foreman-tail --since today
```

Press `Ctrl+C` to stop following the logs.
