# Quadlet Testing

This repository is testing a deployment of Foreman and Katello using Podman quadlet's and Ansible.

## Development

To setup the environment, run the setup script which will create a virtualenv and populate all of the dependencies:

```
./setup-environment
source .venv/bin/activate
```

## Deployment

This setup uses Vagrant to create a basic VM for running the deployment on:

```
./setup-environment
source .venv/bin/activate
./forge vms start
./foremanctl deploy
```

To teardown the environment:

```
./forge vms stop
```

## Testing

Ensure you have a deployment. Now run the tests:

```
./forge test
```

## Release

To create a release, bump `VERSION`, update `foremanctl.spec`, create a commit and tag.
It must follow the x.y.z pattern without any prefix.

```
VERSION=x.y.z
echo $VERSION > VERSION
sed -i -E "/^Version:/ s#[0-9.]+#$VERSION#" foremanctl.spec
git commit -m "Release $VERSION" VERSION foremanctl.spec
git tag -s "$VERSION" -m "Release $VERSION"
git push --follow-tags
```

This will create a GitHub release and attach the created tarball to it.

Once that is done, you can upload `foremanctl.spec` to the [@theforeman/foremanctl COPR](https://copr.fedorainfracloud.org/coprs/g/theforeman/foremanctl/).

## Service Configuration

Configuration files for services are stored as [podman secrets](https://docs.podman.io/en/latest/markdown/podman-secret-create.1.html) and mounted into the container at the expected locations. These configuration files can be listed:

```
podman secret ls
```

To view an individual configuration file:

```
podman secret inspect --showsecret --format "{{.SecretData}}" <secret-name>
```

### Naming Convention

Each secret, whether a configuration file or value shall following the following conventions:

Naming:

    * Config files: <role_namespace>-<filename>-<extension>
    * Strings: <role_namespace>-<descriptive_name>

Naming when additional application context is required that does not match the `role_namespace`:

    * Config files: <role_namespace>-<app>-<filename>-<extension>
    * Strings: <role_namespace>-<app>-<descriptive_name>

Each shall contain labels that provide additional metadata:

    * Config Files
        - filename: <name of file>.<extension>
        - app: <name of application that uses the configuration file>
    * Strings:
        - app: <name of application that uses the string>
