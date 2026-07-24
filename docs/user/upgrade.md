# Upgrading foremanctl

Foremanctl releases bundle specific versions of Foreman with version-compatible dependencies and plugins.

For nearly all install situations, upgrading your Foreman server should be approached through upgrading foremanctl. Scroll to the correct procedure below which matches your installation environment type (RPM, disconnected RPM, source).

## Upgrading foremanctl from RPM install

All steps must be run as root user. We also recommend that a `foremanctl health` check is run before these steps.

1. We recommend setting up a dnf versionlock for foremanctl if control over Foreman versioning is critical to your use case. If applicable, please take a moment to review your current versionlock configuration:
    - `dnf versionlock list` - View the current versionlock configuration
    - `dnf versionlock add 'foremanctl-X.*'` - Lock upgrades to a certain X-stream (replace with exact X version).
    - `dnf versionlock add 'foremanctl-X.Y.*'` - Lock upgrades to a certain Y-stream (replace with exact X.Y version).
    - `dnf versionlock delete foremanctl` - Remove any foremanctl versionlock.
2. We recommend a full foremanctl backup before all upgrade operations. Run `foremanctl backup <filepath for backup>`.  Please see [Backup](backup.md) for more information on this process.
3. Run upgrade tasks by re-deploying foremanctl with the deploy command: `foremanctl deploy [...]`. Please see [Parameters](parameters.md) for additional deploy options.

This final deploy command will pull new images and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.

## Upgrading foremanctl from disconnected RPM install

All below steps must be run as root user. We also recommend that a `foremanctl health` check is run before these steps.

1. Stage the foremanctl RPM package
    - The Foreman repository is needed for dependencies related to the foremanctl RPM.
    - The foremanctl RPM must be available in a repository accessible to your disconnected Foreman server. Please transfer the RPM to your disconnected system via an available transport mechanism (USB drive, rsync over a bastion, etc.).
    - The foremanctl RPM can be downloaded from TODO: TBD
    - Once staged, `dnf info foremanctl` will resolve as in a connected environment.
2. Stage the required container images
    - On a connected machine, pull all required images with `foremanctl pull-images`.
    - Confirm the correct images were downloaded by running `podman images` on both the connected and disconnected machines. All images from your previous-version disconnected environment should be present on the connected environment. If images are missing, ensure parameters are identical between machines.
    - On the connected environment, run `podman save $(podman images --format "{{.Repository}}:{{.Tag}}" | tr '\n' ' ') -o <filename>.tar` to export all downloaded images as a tarball.
    - Transfer the tar file to your disconnected environment via an available transport mechanism.
    - Run `podman load -i <filename>.tar` to stage the required images.
3. Complete the [Upgrading foremanctl from RPM install](#upgrading-foremanctl-from-rpm-install) section above to install from locally staged packages and images.

## Recovering from a failed upgrade

In the event of a failed upgrade, don't panic! A failed deploy will typically reveal the details of what went wrong and can give hints regarding the nature of your issue. Here are some troubleshooting steps:

#### (RPM install) `dnf upgrade foremanctl` had "Nothing to do"
Run `dnf versionlock list` to see if your system is configured to allow X or Y version upgrades. Update the versionlock using the steps above.

#### `foremanctl deploy` could not pull images from remote
Ensure that https://quay.io is unblocked on your network. You can manually open https://quay.io/foreman/foreman in a browser to view available images.

#### I'd like to roll back to a known working version (RPM install)
`dnf downgrade foremanctl-X.Y.Z` will roll back your foremanctl install to the requested version. Please follow instructions in our [Restore Guide](restore.md) to restore your system to a working state.

TODO: this section could present the information better imho. Can you think of a way to put the roll back instructions into the main document above.
