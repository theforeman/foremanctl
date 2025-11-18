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


def foreman_plugins(value):
    dependencies = [FEATURE_MAP.get(feature, {}).get('dependencies', []) for feature in filter_content(value) if feature not in BASE_FEATURES]
    dependencies = list(set([dep for deplist in dependencies for dep in deplist]))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman', {}).get('plugin_name') for feature in (value + dependencies) if feature not in BASE_FEATURES]
    return compact_list(plugins)


def known_foreman_plugins(_value):
    plugins = [FEATURE_MAP.get(feature).get('foreman', {}).get('plugin_name') for feature in FEATURE_MAP.keys()]
    return compact_list(plugins)


class FilterModule(object):
    '''foremanctl filters'''

    def filters(self):
        return {
            'features_to_foreman_plugins': foreman_plugins,
            'known_foreman_plugins': known_foreman_plugins,
        }
