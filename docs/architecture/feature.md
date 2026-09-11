# Feature

## Ansible

The Ansible feature sets up the integration between Foreman and Ansible. On
Foreman side it enables the
[foreman_ansible](https://github.com/theforeman/foreman_ansible) plugin.

Ansible depends on Remote Execution, so enabling `ansible` implicitly enables
`remote-execution` feature as well.

### Interaction with foreman-proxy feature
When the feature is enabled on the Foreman proxy, the [`foreman_proxy`
role](../../src/roles/foreman_proxy/tasks/feature/ansible.yaml) enables the
[smart_proxy_ansible](https://github.com/theforeman/smart_proxy_ansible) plugin
and creates the following files and mounts:

| Host-side object | Container path | Binding | Purpose |
| --- | --- | --- | --- |
| Podman secret `foreman-proxy-ansible-yml` | `/etc/foreman-proxy/settings.d/ansible.yml` | `Secret=...,type=mount` | Enables the Smart Proxy Ansible plugin and points it at its working directory and environment file. |
| Podman secret `foreman-proxy-ansible-env` | `/etc/foreman-proxy/ansible.env` | `Secret=...,type=mount` | Supplies the environment used when the proxy runs Ansible. |
| `/var/lib/foreman-proxy/ansible` | `/etc/ansible` | `Volume=...:ro,Z,U` | Makes roles, collections, and `ansible.cfg` available inside the proxy container. |

The host-side Ansible directory is initialized with these entries:

```text
/var/lib/foreman-proxy/ansible/
├── ansible.cfg       # created empty if it does not already exist
├── collections/
└── roles/
```

The container therefore reads the host directory at `/etc/ansible`, while
operators use the persistent host path under `/var/lib/foreman-proxy/ansible`.
In that directory, `ansible.cfg` can be edited freely, but can never override
the values placed by `foremanctl` into the `foreman-proxy-ansible-env` secret.
User-provided ansible roles and collections are expected to be placed in the
`roles` and `collections` directories.

Proxy sources an environment file passed to the container as a secret, which
configures the Ansible roles and collections search paths under `/etc/ansible`
and `/usr/share`, and sets the Foreman URL and certificate paths. The Foreman
Proxy base container mounts those certificate files as its own secrets; the
Ansible environment file refers to those existing mounts rather than creating
copies of the certificates.
