# Upgrading foremanctl

Foremanctl releases are locked to specific Foreman images with version-compatible dependencies and plugins. Your system's installed `foreman-release` repository configuration RPM locks your system to the correct foremanctl version, which in turn will pull the correct Foreman images. For nearly all install situations, upgrading your Foreman server should be approached through upgrading `foremanctl`.

Foreman MUST be upgraded one release at a time (e.g. 3.19 -> 3.20).

Scroll to the correct procedure below which matches your installation environment type ([RPM](#upgrading-foremanctl-from-rpm-install) and [disconnected RPM](#upgrading-foremanctl-from-disconnected-rpm-install)).

# Upgrading foremanctl y-stream (ex. x.1 to x.2)

## Upgrading foremanctl from RPM install

All steps must be run as root user.

1. Optional: Run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before upgrade. See [Backup and Restore](backup-restore.md).
3. Manually update your Foreman Release repository to the next Foreman Y release:
    - `dnf upgrade https://yum.theforeman.org/releases/<next-version>/el9/x86_64/foreman-release.rpm`
    - Example: Foreman 3.19 -> 5.0 upgrades would use `dnf upgrade https://yum.theforeman.org/releases/5.0/el9/x86_64/foreman-release.rpm`.
4. Update all packages to their latest versions:
    - `dnf upgrade`
5. Optional Pre-pull container images to reduce downtime during deploy:
    - `foremanctl pull-images`
    - This step is optional but recommended. Services can continue running while images are pulled, reducing the downtime window during the deploy.
6. Stop the existing Foreman services:
    - `systemctl stop foreman.target`
7. Run upgrade tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy` 
    - Please see [Parameters](parameters.md) for additional deployment options.
    - This deploy command will pull new images (if not already pulled in the previous step) and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.

## Upgrading foremanctl from disconnected RPM install

All steps must be run as root user.

1. Optional: On your disconnected environment, run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before upgrade. See [Backup and Restore](backup-restore.md).
3. On an internet connected environment, install the same Foreman Release repository as your disconnected environment:
    - `dnf install https://yum.theforeman.org/releases/<current-version>/el9/x86_64/foreman-release.rpm`
    - This installs and enables `foreman` and `foreman-plugins` repositories.
4. If using `hammer` feature: On a connected environment, install the Katello repository:
    - `dnf install https://yum.theforeman.org/katello/<current-version>/katello/el9/x86_64/katello-repos-latest.rpm`
5. On an internet connected environment, create a local mirror of the Foreman repository:
    - `reposync -n -p /path/to/mirror --download-metadata --repoid=foreman`
    - If using the `hammer` feature, add `--repoid=foreman-plugins --repoid=katello` to the previous command.
6. On an internet connected environment, install foremanctl and configure it identically to your disconnected environment:
    - `dnf install foremanctl`
    - Note the version of foremanctl which installed.
    - Configure your internet connected foremanctl to use the same features as your disconnected environment.
7. On an internet connected environment, pull updated container images:
    - `foremanctl pull-images`
    - Confirm the correct images were downloaded by running `podman images`. All images from your previous-version disconnected environment should be present on the internet connected environment. If images are missing, ensure foremanctl features parameters are identical between environments.
    - Run `podman save $(podman images --format "{{.Repository}}:{{.Tag}}" | tr '\n' ' ') -o <filename>.tar` to export all downloaded images as a tarball.
8. Using an available transport mechanism, move the following to your disconnected environment:
    - The `foreman` repo mirror and contents (contains the upgraded foremanctl package).
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
12. Stop the existing Foreman services:
    - `systemctl stop foreman.target`
13. Run upgrade tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy`
