httpd Role
==========

Deploys Apache httpd as the reverse proxy for Foreman and Pulp.

Journal logging
---------------

Apache access and error logs are sent to journald via `systemd-cat`.
Each vhost uses its own syslog identifier (filter with `journalctl -t`).

| Identifier | VHost | Log type | Typical content |
|------------|-------|----------|-------------------|
| `httpd-access` | HTTP (80) | Access | All requests, including 404 responses |
| `httpd-error` | HTTP (80) | Error | Server/proxy errors (backend unreachable, malformed requests) |
| `httpd-ssl-access` | HTTPS (443) | Access | All requests, including 404 responses |
| `httpd-ssl-error` | HTTPS (443) | Error | Server/proxy errors |

Pulp-only or mirror deployments use `pulpcore-ssl-access`, `pulpcore-ssl-error`,
`mirror-access`, and `mirror-error` instead.

Examples:

```bash
# Access log (404s, normal traffic)
journalctl -t httpd-ssl-access --since "10 min ago"
journalctl -t httpd-access | grep "/pub/"

# Error log (proxy failures, malformed requests)
journalctl -t httpd-ssl-error --since "1 hour ago"
```

