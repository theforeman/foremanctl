# Upgrading foremanctl

Foremanctl releases are locked to specific Foreman images with version-compatible dependencies and plugins. Your system's installed `foreman-release` repository configuration RPM locks your system to the correct foremanctl version, which in turn will pull the correct Foreman images. For nearly all install situations, upgrading your Foreman server should be approached through upgrading `foreman-release` and `foremanctl`.

Foreman MUST be upgraded one release at a time (e.g. 3.19 -> 3.20).

Scroll to the correct procedure below which matches your installation environment type (RPM and disconnected RPM).

# Upgrading foremanctl y-stream (ex. x.1 to x.2)

## Upgrading foremanctl from RPM install

All steps must be run as root user.

1. Run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before upgrade. See [Backup and Restore](backup-restore.md).
3. Manually update your Foreman Release repository to the next Foreman Y release:
    - `dnf upgrade https://yum.theforeman.org/releases/<next-version>/el9/x86_64/foreman-release.rpm`
    - Example: Foreman 3.19 -> 3.20 upgrades would use `dnf upgrade https://yum.theforeman.org/releases/3.20/el9/x86_64/foreman-release.rpm`.
4. Upgrade the foremanctl package:
    - `dnf upgrade foremanctl`
5. (Optional) Pre-pull container images to reduce downtime during deploy:
    - `foremanctl pull-images`
    - This step is optional but recommended. Services can continue running while images are pulled, reducing the downtime window during the deploy.
6. Run upgrade tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy` 
    - Please see [Parameters](parameters.md) for additional deployment options.
    - This deploy command will pull new images (if not already pulled in the previous step) and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.

## Upgrading foremanctl from disconnected RPM install

All steps must be run as root user.

1. On your disconnected environment, run `foremanctl health` to ensure your existing Foreman server is healthy. Correct any issues before continuing.
2. Consider backing up your Foreman environment before upgrade. See [Backup and Restore](backup-restore.md).
3. On a connected machine, install the Foreman Release repository for the next Foreman Y release:
    - `dnf install https://yum.theforeman.org/releases/<next-version>/el9/x86_64/foreman-release.rpm`
    - Example: Foreman 3.19 -> 3.20 upgrades would use `dnf install https://yum.theforeman.org/releases/3.20/el9/x86_64/foreman-release.rpm`.
4. On a connected machine, create a local mirror of the foreman repository:
    - `reposync -n -p /path/to/mirror --download-metadata --repoid=foreman`
5. On a connected machine, install foremanctl and configure it identically to your disconnected environment:
    - `dnf install foremanctl`
    - Note the version of foremanctl which installed.
    - Configure your connected foremanctl to use the same features as your disconnected environment.
6. On a connected machine, pull required images and prepare them for transfer:
    - `foremanctl pull-images`
    - Confirm the correct images were downloaded by running `podman images`. All images from your previous-version disconnected environment should be present on the connected environment. If images are missing, ensure foremanctl features parameters are identical between machines.
    - Run `podman save $(podman images --format "{{.Repository}}:{{.Tag}}" | tr '\n' ' ') -o <filename>.tar` to export all downloaded images as a tarball.
7. Using an available transport mechanism, move the following to your disconnected environment:
    - The foreman repo mirror and contents (contains foremanctl).
    - The foremanctl container image tarball.
8. On the disconnected environment, set up the repository mirrors:
    - Copy the mirrored directory to a stable location (e.g., `/var/repos/foreman`).
    - Redirect the existing repository configuration to use your local mirror:
      - `dnf config-manager --setopt=foreman.baseurl=file:///var/repos/foreman --save`
    - Verify the mirror is serving the correct package version with `dnf info foremanctl`. This version should match step 5.
9. On the disconnected environment, stage the required container images:
    - `podman load -i <filename>.tar`
10. On the disconnected environment, upgrade the foremanctl package:
    - `dnf upgrade foremanctl`
11. Run upgrade tasks by re-deploying your Foreman environment: 
    - `foremanctl deploy` 
    - Please see [Parameters](parameters.md) for additional deployment options.
    - This deploy command will pull new images and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.
