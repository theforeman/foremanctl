# Foreman Installation Guide

## Authenticated Registry

If you need to pull images from private or authenticated container registries, you can configure registry authentication using Podman's auth file.

### Setting up Registry Authentication

1. **Login to your registry** using Podman and save credentials to the default auth file location:
   ```bash
   podman login <registry> --authfile=/etc/foreman/registry-auth.json
   ```

2. **Ensure proper permissions** on the auth file:
   ```bash
   sudo chmod 600 /etc/foreman/registry-auth.json
   sudo chown root:root /etc/foreman/registry-auth.json
   ```

3. **Deploy as usual** - foremanctl will automatically detect and use the authentication file:
   ```bash
   ./foremanctl deploy
   ```
