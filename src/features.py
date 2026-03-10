#!/usr/bin/env python3
"""Display enabled and available features for Foreman deployment."""
import yaml
import pathlib
import os

GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

BASE_DIR = pathlib.Path(__file__).resolve().parent
STATE_DIR = pathlib.Path(os.environ.get('OBSAH_STATE', '.var/lib/foremanctl'))


def load_yaml(path: pathlib.Path) -> dict:
    """Load YAML file, return empty dict if not found."""
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def get_feature_components(meta: dict) -> str:
    """Return comma-separated string of components a feature touches."""
    parts = []
    if meta.get('foreman'):
        parts.append('foreman')
    if meta.get('foreman_proxy'):
        parts.append('proxy')
    if meta.get('hammer'):
        parts.append('hammer')
    return ','.join(parts) if parts else '-'

def main():
    features_yaml = BASE_DIR / "features.yaml"
    all_features = load_yaml(features_yaml)

    # Load persisted parameters
    params_yaml = STATE_DIR / "parameters.yaml"
    params = load_yaml(params_yaml)

    flavor = params.get('flavor', 'katello')
    added_features = params.get('features', [])

    # Load flavor configuration
    flavor_file = BASE_DIR / f"vars/flavors/{flavor}.yml"
    flavor_config = load_yaml(flavor_file)
    flavor_features = flavor_config.get('flavor_features', [])

    enabled_features = flavor_features + added_features

    print(f"{'FEATURE':<25} {'STATE':<12} {'BASE':<20} DESCRIPTION")

    # Separate enabled and available
    enabled_list = []
    available_list = []

    for name in sorted(all_features.keys()):
        meta = all_features[name] or {}

        # Skip internal features
        if meta.get('internal', False):
            continue

        components = get_feature_components(meta)
        description = meta.get('description', '')

        if name in enabled_features:
            enabled_list.append((name, 'enabled', components, description))
        else:
            available_list.append((name, 'available', components, description))

    for name, state, components, description in enabled_list:
        print(f"{name:<25} {GREEN}{state:<12}{RESET} {components:<20} {description}")

    for name, state, components, description in available_list:
        print(f"{name:<25} {DIM}{state:<12}{RESET} {DIM}{components:<20}{RESET} {description}")

    print()
    enabled_count = len(enabled_list)
    total_count = len(enabled_list) + len(available_list)
    print(f"{total_count} features listed ({enabled_count} enabled, {len(available_list)} available).")


if __name__ == "__main__":
    main()
