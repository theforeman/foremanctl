# Updating foremanctl

Foremanctl releases are locked to specific Foreman images with version-compatible dependencies and plugins. Over time, the contents of a particular Foreman image may be updated to reflect newer Foreman patches. The update process first updates your system to the latest foremanctl z-stream (if applicable), then instructs foremanctl to pull the latest container images. This procedure will never migrate your Foreman container beyond z-stream patches.

Scroll to the correct procedure below which matches your installation environment type ([RPM](#updating-foremanctl-from-rpm-install) and [disconnected RPM](#updating-foremanctl-from-disconnected-rpm-install)).

# Updating foremanctl z-stream (x.y.1, x.y.2)

## Updating foremanctl from an connected RPM install

All steps must be run as root user.

1. Optional: Run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before update. See [Backup and Restore](backup-restore.md).
3. Update all packages to their latest versions:
    - `dnf upgrade`
    - There may not be a new release available for foremanctl; that is okay. Foreman images are updated through step 4.
4. Update the running deployment:
    - `foremanctl update`
    - This pre-pulls the updated container images while the existing services are still running, then stops all Foreman services and sockets and redeploys the environment using the persisted deployment parameters.
    - If image pulling fails, the existing services remain running. If deployment fails after services are stopped, correct the reported problem and run `foremanctl deploy` to finish the update.

## Updating foremanctl from disconnected RPM install

All steps must be run as root user.

1. Optional: On your disconnected environment, run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before update. See [Backup and Restore](backup-restore.md).
3. On an internet connected environment, install the same Foreman Release repository as your disconnected environment:
    - `dnf install https://yum.theforeman.org/releases/<current-version>/el9/x86_64/foreman-release.rpm`
    - This installs and enables the `foreman` and `foreman-plugins` repositories.
4. If using `hammer` feature: On an internet connected environment, install the Katello repository:
    - `dnf install https://yum.theforeman.org/katello/<current-version>/katello/el9/x86_64/katello-repos-latest.rpm`
    - This installs the `katello`, `candlepin`, and `pulpcore` repositories.
5. On an internet connected environment, create a local mirror of the installed repositories:
    - `reposync -n -p /path/to/mirror --download-metadata --repoid=foreman`
    - If using the `hammer` feature, add `--repoid=foreman-plugins --repoid=katello` to the previous command.
6. On an internet connected environment, install foremanctl and configure it identically to your disconnected environment:
    - `dnf install foremanctl`
    - Note the version of foremanctl which installed.
    - Configure your internet connected foremanctl to use the same features as your disconnected environment.
7. On an internet connected environment, pull updated container images:
    - `foremanctl pull-images`
    - Container image tags are updated over time for a given Foreman X.Y release to include the bug fixes and security patches.
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
11. On the disconnected environment, update all packages to their latest versions:
    - `dnf upgrade`
12. Update the running deployment using the preloaded images:
    - `foremanctl update --air-gapped`
    - Air-gapped mode skips registry access, stops all Foreman services and sockets, and redeploys the environment using the persisted deployment parameters.
    - If deployment fails after services are stopped, correct the reported problem and run `foremanctl deploy --air-gapped` to finish the update.
