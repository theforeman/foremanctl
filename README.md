# Foreman deployment using Podman and Ansible

This repository provides tooling for a deployment of Foreman and Katello using Podman quadlets and Ansible.

## Compatibility

### Foreman

Foreman 3.17 (with Katello 4.19, Pulp 3.85 and Candlepin 4.6).

### Ansible

`ansible-core` 2.14 as present in CentOS Stream 9.

## Packages

### RPM

Snapshot RPM packages of `foremanctl` and its dependencies can be found in the [`@theforeman/foremanctl` copr](https://copr.fedorainfracloud.org/coprs/g/theforeman/foremanctl/).

```
dnf copr enable @theforeman/foremanctl rhel-9-x86_64
dnf install foremanctl
```
