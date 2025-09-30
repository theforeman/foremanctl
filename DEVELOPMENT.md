# Development

## Requirements

* Vagrant - 2.2+
* Ansible - 2.14+
* [Vagrant Libvirt provider plugin](https://github.com/vagrant-libvirt/vagrant-libvirt)
* Virtualization enabled in BIOS

Follow [instruction](https://github.com/theforeman/forklift/blob/master/docs/vagrant.md) to install vagrant


## Development environment

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
./foremanctl deploy --foreman-initial-admin-password=changeme
```

## Deploy hammer (optional)

```
./forge setup-repositories
./foremanctl setup-hammer
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

[!NOTE]
This will trigger all the tests so hammer tests will fail if you don't have [hammer setup](#deploy-hammeroptional)

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
