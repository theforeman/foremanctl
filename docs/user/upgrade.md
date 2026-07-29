# Upgrading foremanctl

Foremanctl releases bundle specific versions of Foreman with version-compatible dependencies and plugins.

For nearly all install situations, upgrading your Foreman server should be approached through upgrading foremanctl. Scroll to the correct procedure below which matches your installation environment type (RPM, disconnected RPM, source).

## Upgrading foremanctl from RPM install

All steps must be run as root user. We also recommend that a `foremanctl health` check is run before these steps.

1. Update the Foreman repository to the target version for the X or Y stream upgrades:
    - `dnf upgrade https://yum.theforeman.org/releases/<target-version>/el9/x86_64/foreman-release.rpm`
2. Upgrade the foremanctl package:
    - `dnf upgrade foremanctl`
3. Run upgrade tasks by re-deploying: `foremanctl deploy`. Please see [Parameters](parameters.md) for additional deploy options.

This final deploy command will pull new images and run all upgrade jobs required by Foreman, its dependencies, and your configured plugins. Expect this deploy to take longer than typical deploys.

## Upgrading foremanctl from disconnected RPM install

All below steps must be run as root user. We also recommend that a `foremanctl health` check is run before these steps.

Disconnected users should also create a local repository mirror of foreman, an example of this from Red Hat is linked here https://access.redhat.com/solutions/7019225.

1. Stage the foremanctl RPM package
    - The Foreman repository is needed for dependencies related to the foremanctl RPM.
    - The foremanctl RPM must be available in a repository accessible to your disconnected Foreman server. Please transfer the RPM to your disconnected system via an available transport mechanism (USB drive, rsync over a bastion, etc.).
    - The foremanctl RPM can be downloaded from `https://yum.theforeman.org`
    - Once staged, `dnf info foremanctl` will resolve as in a connected environment.
2. Stage the required container images
    - On a connected machine, pull all required images with `foremanctl pull-images`.
    - Confirm the correct images were downloaded by running `podman images` on both the connected and disconnected machines. All images from your previous-version disconnected environment should be present on the connected environment. If images are missing, ensure parameters are identical between machines.
    - On the connected environment, run `podman save $(podman images --format "{{.Repository}}:{{.Tag}}" | tr '\n' ' ') -o <filename>.tar` to export all downloaded images as a tarball.
    - Transfer the tar file to your disconnected environment via an available transport mechanism.
    - Run `podman load -i <filename>.tar` to stage the required images.
3. Complete the [Upgrading foremanctl from RPM install](#upgrading-foremanctl-from-rpm-install) section above starting from step 3 to install from locally staged packages and images.

## Recovering from a failed upgrade

In the event of a failed upgrade, don't panic! A failed deploy will typically reveal the details of what went wrong and can give hints regarding the nature of your issue. Here are some troubleshooting steps:

#### (RPM install) `dnf upgrade foremanctl` had "Nothing to do"
Run `dnf versionlock list` to see if your system is configured to allow X or Y version upgrades. Update the versionlock using the steps above.

#### `foremanctl deploy` could not pull images from remote
Ensure that https://quay.io is unblocked on your network. You can manually open https://quay.io/foreman/foreman in a browser to view available images.
