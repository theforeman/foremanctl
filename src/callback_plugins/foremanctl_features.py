from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
import pathlib
import yaml
import os

BASE_DIR = pathlib.Path(__file__).parent.parent
STATE_DIR = pathlib.Path(os.environ.get('OBSAH_STATE', '.var/lib/foremanctl'))

def load_yaml(path: pathlib.Path) -> dict:
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


class CallbackModule(CallbackBase):
    """Features listing callback."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'foremanctl_features'

    def __init__(self):
        super().__init__()
        self.feature_metadata = self._load_features_metadata()

    def _load_features_metadata(self):
            features_yaml = BASE_DIR / 'features.yaml'
            return load_yaml(features_yaml)

    def v2_runner_on_ok(self, result):
        if result._task.action in ('ansible.builtin.debug', 'debug'):
            self._display_features()

    def _display_features(self):
        params_yaml = STATE_DIR / "parameters.yaml"
        params = load_yaml(params_yaml)

        flavor = params.get('flavor')
        added_features = params.get('features', [])

        flavor_file = BASE_DIR / f"vars/flavors/{flavor}.yml"
        flavor_config = load_yaml(flavor_file)
        flavor_features = flavor_config.get('flavor_features', [])

        enabled_features = flavor_features + added_features

        enabled_list = []
        available_list = []

        for name in sorted(self.feature_metadata.keys()):
            meta = self.feature_metadata.get(name, {}) or {}

            if meta.get('internal', False):
                continue

            description = meta.get('description', '')

            if name in enabled_features:
                enabled_list.append((name, 'enabled', description))
            else:
                available_list.append((name, 'available', description))

        self._display.display(f"{'FEATURE':<25} {'STATE':<12} DESCRIPTION")

        for name, state, description in enabled_list:
            self._display.display(f"{name:<25} {state:<12} {description}")

        for name, state, description in available_list:
            self._display.display(f"{name:<25} {state:<12} {description}")

        total = len(enabled_list) + len(available_list)
        self._display.display("")
        self._display.display(
            f"{total} features listed ({len(enabled_list)} enabled, {len(available_list)} available)."
        )
