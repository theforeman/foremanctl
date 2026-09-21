# Updating foremanctl

Foremanctl releases are locked to specific Foreman images with version-compatible dependencies and plugins. Over time, the contents of a particular Foreman image may be updated to reflect newer Foreman patches. The update process first updates your system to the latest foremanctl z-stream (if applicable), then instructs foremanctl to pull the latest container images. This procedure will never migrate your Foreman container beyond z-stream patches.

Scroll to the correct procedure below which matches your installation environment type ([RPM](#updating-foremanctl-from-rpm-install) and [disconnected RPM](#updating-foremanctl-from-disconnected-rpm-install)).

# Updating foremanctl z-stream (x.y.1, x.y.2)

## Updating foremanctl from RPM install

All steps must be run as root user.

1. Optional: Run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before update. See [Backup and Restore](backup-restore.md).
3. Run dnf upgrade:
    - `dnf upgrade`
    - There may not be a new release available for foremanctl; that is okay. Foreman images are updated through step 4.
4. Pull updated container images:
    - `foremanctl pull-images`
    - Container image tags remain constant over time for a given X.Y foremanctl release. The container images themselves, however, are frequently updated with bug fixes and security patches. Pulling images ensures the newest Foreman Z stream update.
5. Stop the existing Foreman services:
    - `systemctl stop foreman.target`
6. Run update tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy` 

## Updating foremanctl from disconnected RPM install

All steps must be run as root user.

1. Optional: On your disconnected environment, run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before update. See [Backup and Restore](backup-restore.md).
3. On a internet connected environment, install the same Foreman Release repository as your disconnected environment:
    - `dnf install https://yum.theforeman.org/releases/<current-version>/el9/x86_64/foreman-release.rpm`
    - This installs and enables the `foreman` and `foreman-plugins` repositories.
4. If using `hammer` feature: On a internet connected environment, install the Katello repository:
    - `dnf install https://yum.theforeman.org/katello/<current-version>/katello/el9/x86_64/katello-repos-latest.rpm`
    - This installs the `katello`, `candlepin`, and `pulpcore` repositories.
5. On a internet connected environment, create a local mirror of the installed repositories:
    - `reposync -n -p /path/to/mirror --download-metadata --repoid=foreman`
    - If using the `hammer` feature, add `--repoid=foreman-plugins --repoid=katello` to the previous command.
6. On a internet connected environment, install foremanctl and configure it identically to your disconnected environment:
    - `dnf install foremanctl`
    - Note the version of foremanctl which installed.
    - Configure your internet connected foremanctl to use the same features as your disconnected environment.
7. On a internet connected environment, pull updated container images:
    - `foremanctl pull-images`
    - Container image tags remain constant over time for a given X.Y foremanctl release. The container images themselves, however, are frequently updated with bug fixes and security patches. Pulling images ensures the newest Foreman update is running.
    - Confirm the correct images were downloaded by running `podman images`. All images from your previous-version disconnected environment should be present on the internet connected environment. If images are missing, ensure foremanctl features parameters are identical between environments.
    - Run `podman save $(podman images --format "{{.Repository}}:{{.Tag}}" | tr '\n' ' ') -o <filename>.tar` to export all downloaded images as a tarball.
8. Using an available transport mechanism, move the following to your disconnected environment:
    - The `foreman` repo mirror (contains the updated foremanctl package, if applicable).
    - The foremanctl container image tarball.
9. On the disconnected environment, set up the repository mirrors:
    - Copy the mirrored directory to a stable location (e.g., `/var/repos/foreman`).
    - Redirect the existing repository configuration to use your local mirror:
      - `dnf config-manager --setopt=foreman.baseurl=file:///var/repos/foreman --save`
    - Verify the mirror is serving the correct package version with `dnf info foremanctl`. This version should match step 6.
    - If applicable, repeat for `foreman-plugins` and `katello`.
10. On the disconnected environment, stage the updated container images:
    - `podman load -i <filename>.tar`
11. On the disconnected environment, run dnf upgrade:
    - `dnf upgrade`
12. Stop the existing Foreman services:
    - `systemctl stop foreman.target`
13. Run update tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy`
