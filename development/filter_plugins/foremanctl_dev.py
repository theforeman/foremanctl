from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pathlib
import sys
import yaml

# Make src filter_plugins importable to reuse dependency resolution logic
# and the shared FEATURE_MAP, avoiding duplication.
_src_filter_plugins = str(pathlib.Path(__file__).parent.parent.parent / 'src' / 'filter_plugins')
if _src_filter_plugins not in sys.path:
    sys.path.insert(0, _src_filter_plugins)

from foremanctl import FEATURE_MAP, filter_features, get_dependencies_for_feature  # noqa: E402

_dev_features_yaml = pathlib.Path(__file__).parent.parent / 'features.yaml'


def _deep_merge(base, override):
    """Recursively merge override into base, returning the merged dict."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# Deep-merge development-specific feature extensions into the shared FEATURE_MAP.
# This adds development: blocks to existing src/ features and introduces
# dev-only features with full definitions.
with _dev_features_yaml.open() as _f:
    for _feature, _data in yaml.safe_load(_f).items():
        if _feature in FEATURE_MAP:
            FEATURE_MAP[_feature] = _deep_merge(FEATURE_MAP[_feature], _data)
        else:
            FEATURE_MAP[_feature] = _data


def _resolve_features(value):
    """Resolve feature list including transitive dependencies, preserving order."""
    all_features = list(filter_features(value))
    deps = set()
    for f in all_features:
        deps.update(get_dependencies_for_feature(f))
    seen = set()
    result = []
    for f in list(filter_features(list(value) + list(deps))):
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result


def dev_plugins(value):
    """Return list of development plugin configs for enabled features and their dependencies.

    Each entry is the development: block from features.yaml for features that have
    any development data (foreman, hammer, or foreman_proxy). The calling tasks use
    conditional guards to skip entries that lack a specific component.
    """
    plugins = []
    for feature in _resolve_features(value):
        dev_data = FEATURE_MAP.get(feature, {}).get('development', {})
        if dev_data:
            plugins.append(dev_data)
    return plugins


class FilterModule(object):
    '''foremanctl development filters'''

    def filters(self):
        return {
            'features_to_dev_plugins': dev_plugins,
        }
