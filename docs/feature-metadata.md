# Feature Metadata

Users want to enable abstract features, which means the deployment needs to know how to translate a feature name to a set of changes (configuration files, services, etc).

The metadata is a Hash with the feature name as the key and the feature definition as the value.
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
* `foreman` (_String_): The name of the Foreman plugin to be enabled (via `FOREMAN_ENABLED_PLUGINS`).
  If `roles/foreman/tasks/feature/{{ foreman_plugin }}.yaml` exists, it will be executed to perform any plugin-specific setup.
  * **FIXME**: task file not implemented yet
* `foreman_proxy` (_String_): The name of the Foreman Proxy plugin to be enabled (by deploying `roles/foreman_proxy/templates/settings.d/{{ foreman_proxy_plugin }}.yml.j2` to `/etc/foreman-proxy/settings.d`).
  If `roles/foreman/tasks/feature/{{ foreman_proxy_plugin }}.yaml` exists, it will be executed to perform any plugin-specific setup.
* `hammer` (_String_): The name of the Hammer plugin to be enabled.
  * **FIXME**: Not implemented, right now we use the same list as Foreman plugins, but needs modification for foreman-tasks and friends
* `role` (_String_): The name of the Ansible role that should be executed if this feature is enabled.
* `dependencies` (_Array_ of _String_): List of features that are automatically enabled when the user requests this feature. Usually will point at features with `internal: true`.
* `requirements` (_Array_ of _String_): List of features that are required but can't be automatically enabled (possible reasons: requires manual configuration, can't be enabled after initial deployment).
  Produces an error when the requirement is not met.

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
  requirements:
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
