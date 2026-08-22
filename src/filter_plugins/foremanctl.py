from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

import os
import pathlib

import yaml

BASE_FEATURES = ['hammer', 'foreman-proxy', 'foreman']

_SRC_ROOT = pathlib.Path(__file__).parent.parent
features_yaml = _SRC_ROOT / 'features.yaml'
with features_yaml.open() as features_file:
    FEATURE_MAP = yaml.safe_load(features_file)

# load additional feature files under features.d
_features_d = _SRC_ROOT / 'features.d'
if _features_d.is_dir():
    for _overlay in sorted(_features_d.glob('*.yaml')):
        with _overlay.open() as _overlay_file:
            _extra = yaml.safe_load(_overlay_file) or {}
        FEATURE_MAP.update(_extra)


def compact_list(items):
    return [item for item in items if item is not None]


def filter_content(items):
    return filter(lambda x: not x.startswith('content/'), items)


def filter_base_features(items):
    return filter(lambda x: x not in BASE_FEATURES, items)


def filter_features(items):
    items = filter_content(items)
    items = filter_base_features(items)
    return items


def get_dependencies_for_feature(feature):
    dependencies = set()
    for dependency in FEATURE_MAP.get(feature, {}).get('dependencies', []):
        if dependency not in dependencies:
            dependencies.update(get_dependencies_for_feature(dependency))
        dependencies.add(dependency)
    return dependencies


def get_dependencies(features):
    dependencies = set()
    for feature in features:
        dependencies.update(get_dependencies_for_feature(feature))
    return dependencies


def resolve_dependencies(features):
    """Return features plus all their transitive dependencies."""
    all_features = list(features)
    for dep in get_dependencies(features):
        if dep not in all_features:
            all_features.append(dep)
    return all_features


def foreman_plugins(value):
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman', {}).get('plugin_name') for feature in filter_features(value + dependencies)]
    return compact_list(plugins)


def available_foreman_plugins(_value):
    plugins = [FEATURE_MAP.get(feature).get('foreman', {}).get('plugin_name') for feature in FEATURE_MAP.keys()]
    return compact_list(plugins)


def list_all_features(enabled_features, only_enabled=False):
    enabled_list = []
    available_list = []
    list_internal = os.environ.get('FOREMANCTL_FEATURES_LIST_INTERNAL', '') == 'true'
    for name, meta in FEATURE_MAP.items():
        internal = meta.get('internal', False)
        if internal and not list_internal:
            continue
        description = meta.get('description', '')

        if meta.get('removable', False):
            removable = 'yes'
        else:
            removable = 'no'

        if name in enabled_features:
            enabled_list.append((name, 'enabled', internal, removable, description))
        elif not only_enabled:
            available_list.append((name, 'available', internal, removable, description))

    if not list_internal:
        output = [f"{'FEATURE':<25} {'STATE':<12} {'REMOVABLE':<13} DESCRIPTION"]
        for name, state, _internal, removable, description in enabled_list + available_list:
            output.append(f"{name:<25} {state:<12} {removable:<13} {description}")
    else:
        output = [f"{'FEATURE':<25} {'STATE':<12} {'INTERNAL':<8} {'REMOVABLE':<13} DESCRIPTION"]
        for name, state, internal, removable, description in enabled_list + available_list:
            output.append(f"{name:<25} {state:<12} {internal:<8} {removable:<13} {description}")

    return "\n".join(output)


def is_feature_removable(feature_name):
    """Check if a feature supports removal."""
    return FEATURE_MAP.get(feature_name, {}).get('removable', False)


def invalid_features(features):
    """Return a list of unknown features not defined in features.yaml."""
    return [feature for feature in features if feature not in FEATURE_MAP]


def conflicting_features(features):
    """Return a list of conflict violation strings for enabled features."""
    conflicts = set()
    for feature in features:
        for conflict in FEATURE_MAP.get(feature, {}).get('conflicts', []):
            if conflict in features:
                conflicts.add(tuple(sorted([feature, conflict])))
    return [f"{pair[0]} conflicts with {pair[1]}" for pair in conflicts]


def validate_feature_removals(remove_features, flavor_features):
    """Validate that requested feature removals are allowed.

    Returns a list of error message strings. Empty list means all valid.
    """
    errors = []

    for feature in remove_features:
        if feature in flavor_features:
            errors.append(
                f"Cannot remove '{feature}' — it is a core feature of the current flavor. "
                f"Flavor features cannot be removed."
            )
        elif feature not in FEATURE_MAP:
            errors.append(
                f"Cannot remove unknown feature '{feature}'. "
                f"Run 'foremanctl features' to see available features."
            )
        elif not is_feature_removable(feature):
            errors.append(
                f"Cannot remove feature '{feature}' — this feature does not support removal. "
                f"Run 'foremanctl features' to see which features can be removed."
            )

    return errors


def unsatisfied_dependencies(enabled_features):
    """Check that all feature dependencies are satisfied.

    Returns a list of error strings for missing dependencies.
    """
    errors = []
    enabled_set = set(enabled_features)

    for feature in enabled_features:
        missing = set(get_dependencies_for_feature(feature)) - enabled_set
        if missing:
            errors.append(
                f"Feature '{feature}' requires {', '.join(sorted(missing))} which are not enabled"
            )

    return errors


def hammer_plugins(value):
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('hammer') for feature in filter_features(value + dependencies)]
    return compact_list(plugins)


def foreman_proxy_plugins(value):
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman_proxy', {}).get('plugin_name') for feature in filter_features(value + dependencies)]
    return compact_list(plugins)


def available_foreman_proxy_plugins(_value):
    plugins = [FEATURE_MAP.get(feature).get('foreman_proxy', {}).get('plugin_name') for feature in FEATURE_MAP.keys()]
    return compact_list(plugins)


def has_feature(features, feature):
    """Check if a feature is enabled - exact match, prefix (feature/), or as a transitive dependency."""
    return (feature in features
            or any(f.startswith(feature + '/') for f in features)
            or feature in get_dependencies(list(features)))


def databases_for_features(databases, enabled_features):
    """Return databases whose feature gate matches enabled_features."""
    return [db for db in databases if has_feature(enabled_features, db['feature'])]


def to_postgresql_databases(databases):
    return [{'name': db['database'], 'owner': db['user']} for db in databases]


def to_postgresql_users(databases):
    return [{'name': db['user'], 'password': db['password']} for db in databases]


class FilterModule(object):
    '''foremanctl filters'''

    def filters(self):
        return {
            'features_to_foreman_plugins': foreman_plugins,
            'available_foreman_plugins': available_foreman_plugins,
            'features_to_hammer_plugins': hammer_plugins,
            'features_to_foreman_proxy_plugins': foreman_proxy_plugins,
            'available_foreman_proxy_plugins': available_foreman_proxy_plugins,
            'list_all_features': list_all_features,
            'invalid_features': invalid_features,
            'conflicting_features': conflicting_features,
            'validate_feature_removals': validate_feature_removals,
            'resolve_dependencies': resolve_dependencies,
            'unsatisfied_dependencies': unsatisfied_dependencies,
            'has_feature': has_feature,
            'databases_for_features': databases_for_features,
            'to_postgresql_databases': to_postgresql_databases,
            'to_postgresql_users': to_postgresql_users,
        }
