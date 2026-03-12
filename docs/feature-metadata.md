# Feature Metadata

Users want to enable abstract features, which means the deployment needs to know how to translate a feature name to a set of changes (configuration files, services, etc).

The metadata is a Hash with the feature (using dashes, not underscores if needed) name as the key and the feature definition as the value.
The feature definition itself is again a Hash with the various properties of the feature.

```yaml
feature_one:
  property1: value_of_property1
  property2: value_of_property2
  …
feature_two:
  property1: another_value_of_property1
  property2: another_value_of_property2
  …
…
```

The following properties are defined:
* `description` (_String_): A human-readable description of the feature, can be used in documentation/help output.
* `internal` (_Boolean_): Whether the feature is user visible (shows up in documentation/help) or internal (just to perform additional configuration without user interaction).
* `foreman` (_Hash_): How this feature should be applied on the "main" system that offers the main user interaction via UI/API.
  * `plugin_name` (_String_): The name of the Foreman plugin to be enabled (via `FOREMAN_ENABLED_PLUGINS`).
     If `roles/foreman/tasks/feature/{{ foreman_plugin }}.yaml` exists, it will be executed to perform any plugin-specific setup.
      * **FIXME**: task file not implemented yet
  * `role` (_String_): The name of the Ansible role to be executed if the feature to be placed on the main system but is not implemented as a Foreman plugin.
* `foreman_proxy` (_Hash_): How this feature should be applied to a secondary system that is connected using the Proxy API to the main system.
  * `plugin_name` (_String_): The name of the Foreman Proxy plugin to be enabled (by deploying `roles/foreman_proxy/templates/settings.d/{{ foreman_proxy_plugin }}.yml.j2` to `/etc/foreman-proxy/settings.d`).
    If `roles/foreman/tasks/feature/{{ foreman_proxy_plugin }}.yaml` exists, it will be executed to perform any plugin-specific setup.
  * `role` (_String_): The name of the Ansible role to be executed if the feature is not implemented as a Foreman Proxy plugin.
* `hammer` (_String_): The name of the Hammer plugin to be enabled.
  * **FIXME**: Not implemented, right now we use the same list as Foreman plugins, but needs modification for foreman-tasks and friends
* `dependencies` (_Array_ of _String_): List of features that are automatically enabled when the user requests this feature. Usually will point at features with `internal: true`.

Properties can be omitted.

## Examples

### REX + Dynflow

```yaml
dynflow:
  internal: true
  foreman_proxy: dynflow

remote_execution:
  description: Foreman Remote Execution support
  foreman: foreman_remote_execution
  foreman_proxy: remote_execution_ssh
  dependencies:
    - dynflow
```

The `remote_execution` feature will enable the `foreman_remote_execution` plugin for Foreman and the `remote_execution_ssh` and `dynflow` plugins for Foreman Proxy.
The `dynflow` feature is hidden from the user and only present so that `remote_execution` can pull it in.

### RH Cloud + Katello
```yaml
katello:
  description: Katello
  foreman: katello

rh_cloud:
  description: Foreman RH Cloud
  foreman: foreman_rh_cloud
  dependencies:
    - katello
```

The `rh_cloud` feature can't be enabled unless the `katello` feature is also present in the deployment.

### Katello + tasks
```yaml
foreman-tasks:
  foreman: foreman-tasks
  hammer: foreman_tasks

katello:
  description: Katello
  foreman: katello
  dependencies:
    - foreman-tasks
```

The `foreman-tasks` feature is automatically enabled when the user requests Katello, thus also gaining the Hammer integration for tasks which would be missing if we'd only let the Ruby gem dependency pull in `foreman-tasks`.

### another example

```yaml
dynflow:
  internal: true
  foreman_proxy:
    plugin_name: dynflow

foreman-tasks:
  foreman:
    plugin_name: foreman-tasks
  hammer: foreman_tasks
  dependencies:
    - dynflow

katello:
  description: Katello
  foreman:
    plugin_name: katello
  dependencies:
    - foreman-tasks
   
rh_cloud:
  description: Foreman RH Cloud
  foreman:
    plugin_name: foreman_rh_cloud
  dependencies:
    - katello

remote_execution:
  description: REX
  foreman:
    plugin_name: foreman_remote_execution
  foreman_proxy:
    plugin_name: smart_proxy_remote_execution_ssh
  dependencies:
    - dynflow

openscap:
  description: OpenSCAP
  foreman:
    plugin_name: foreman_openscap
  foreman_proxy:
    plugin_name: smart_proxy_openscap

iop:
  description: IoP
  foreman:
    role: iop_core

container_gateway:
  description: gw is a proxy-only plugin
  foreman_proxy:
    plugin_name: smart_proxy_container_gateway
```
