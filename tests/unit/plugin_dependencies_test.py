from pathlib import Path

import pytest
import yaml
from ansible.errors import AnsibleFilterError
from foreman_development import resolve_foreman_development_plugins

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_remote_execution_resolves_tasks_and_smart_proxy_dynflow():
    defaults_path = REPOSITORY_ROOT / "development/roles/foreman_development/defaults/main.yaml"
    defaults = yaml.safe_load(defaults_path.read_text())
    registry = defaults["foreman_development_plugin_registry"]
    requested = defaults["foreman_development_default_plugins"]

    resolved = resolve_foreman_development_plugins(requested, registry)

    assert resolved.count("foreman_tasks") == 1
    assert resolved.index("foreman_tasks") < resolved.index("foreman_remote_execution")
    assert registry["foreman_tasks"]["smart_proxy"]["name"] == "theforeman/smart_proxy_dynflow"


def test_plugin_dependencies_are_transitive_and_deduplicated():
    registry = {
        "plugin_a": {"dependencies": ["plugin_b", "plugin_c"]},
        "plugin_b": {"dependencies": ["plugin_c"]},
        "plugin_c": {},
    }

    assert resolve_foreman_development_plugins(["plugin_a", "plugin_b"], registry) == [
        "plugin_c",
        "plugin_b",
        "plugin_a",
    ]


def test_plugin_dependency_cycles_are_rejected():
    registry = {"plugin_a": {"dependencies": ["plugin_b"]}, "plugin_b": {"dependencies": ["plugin_a"]}}

    with pytest.raises(AnsibleFilterError, match="Circular.*plugin_a.*plugin_b.*plugin_a"):
        resolve_foreman_development_plugins(["plugin_a"], registry)


def test_unknown_plugin_dependencies_are_rejected():
    with pytest.raises(AnsibleFilterError, match="Unknown Foreman development plugin: missing"):
        resolve_foreman_development_plugins(["missing"], {})
