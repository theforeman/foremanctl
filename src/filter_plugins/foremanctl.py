from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pathlib
import yaml

BASE_FEATURES = ['hammer', 'foreman-proxy', 'foreman']

features_yaml = pathlib.Path(__file__).parent.parent / 'features.yaml'
with features_yaml.open() as features_file:
    FEATURE_MAP = yaml.safe_load(features_file)


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


def foreman_plugins(value):
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman', {}).get('plugin_name') for feature in filter_features(value + dependencies)]
    return compact_list(plugins)


def available_foreman_plugins(_value):
    plugins = [FEATURE_MAP.get(feature).get('foreman', {}).get('plugin_name') for feature in FEATURE_MAP.keys()]
    return compact_list(plugins)


def foreman_proxy_plugins(value):
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman_proxy', {}).get('plugin_name') for feature in filter_features(value + dependencies)]
    return compact_list(plugins)


def available_foreman_proxy_plugins(_value):
    plugins = [FEATURE_MAP.get(feature).get('foreman_proxy', {}).get('plugin_name') for feature in FEATURE_MAP.keys()]
    return compact_list(plugins)


class FilterModule(object):
    '''foremanctl filters'''

    def filters(self):
        return {
            'features_to_foreman_plugins': foreman_plugins,
            'available_foreman_plugins': available_foreman_plugins,
            'features_to_foreman_proxy_plugins': foreman_proxy_plugins,
            'available_foreman_proxy_plugins': available_foreman_proxy_plugins,
        }
