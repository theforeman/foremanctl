from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

BASE_FEATURES = ['hammer', 'foreman-proxy', 'foreman']

FEATURE_MAP = {
    'katello': {
        'foreman': 'katello',
        'foreman_proxy': None
    },
    'remote_execution': {
        'foreman': 'foreman_remote_execution',
        'foreman_proxy': 'remote_execution_ssh',
        'dependencies': ['dynflow']
    },
    'dynflow': {
        'foreman_proxy': 'dynflow'
    },
    'google': {
        'foreman': 'foreman_google',
        'foreman_proxy': None
    },
    'azure_rm': {
        'foreman': 'foreman_azure_rm',
        'foreman_proxy': None
    }
}


def foreman_plugins(value):
    dependencies = [FEATURE_MAP.get(feature, {}).get('dependencies', []) for feature in value if feature not in BASE_FEATURES]
    dependencies = list(set([dep for deplist in dependencies for dep in deplist]))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman') for feature in (value + dependencies) if feature not in BASE_FEATURES]
    return [plugin for plugin in plugins if plugin is not None]


def foreman_proxy_plugins(value):
    dependencies = [FEATURE_MAP.get(feature, {}).get('dependencies', []) for feature in value if feature not in BASE_FEATURES]
    dependencies = list(set([dep for deplist in dependencies for dep in deplist]))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman_proxy') for feature in (value + dependencies) if feature not in BASE_FEATURES]
    return [plugin for plugin in plugins if plugin is not None]


class FilterModule(object):
    ''' foremanctl filters'''

    def filters(self):
        return {
            'features_to_foreman_plugins': foreman_plugins,
            'features_to_foreman_proxy_plugins': foreman_proxy_plugins,
        }
