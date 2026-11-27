import json
import tomllib
from pathlib import Path

import pytest
import yaml
from foremanctl import foreman_plugins
from foremanctl import hammer_plugins
from foremanctl import has_feature
from jinja2 import Environment
from jinja2 import FileSystemLoader

ROOT_DIR = Path(__file__).resolve().parents[2]
ROLE_DIR = ROOT_DIR / "src" / "roles" / "pulp_cli"


@pytest.mark.parametrize("url", [
    "https://satellite.example.com",
    "https://satellite.example.com:443",
])
def test_pulp_cli_config_template(url):
    env = Environment(loader=FileSystemLoader(ROLE_DIR / "templates"))
    env.filters["to_json"] = json.dumps
    values = {
        "pulp_cli_url": url,
        "pulp_cli_client_certificate": '/certs/client "quoted".crt',
        "pulp_cli_client_key": "/private/client.key",
    }
    rendered = env.get_template("cli.toml.j2").render(values)
    config = tomllib.loads(rendered)["cli"]
    assert config == {
        "base_url": url,
        "cert": values["pulp_cli_client_certificate"],
        "key": values["pulp_cli_client_key"],
        "verify_ssl": True,
    }


def test_pulp_cli_requires_pulp_without_foreman_plugins():
    assert has_feature(["pulp-cli"], "pulp")
    assert has_feature(["pulp-cli"], "httpd")
    assert not has_feature([], "pulp-cli")
    assert foreman_plugins(["pulp-cli"]) == []
    assert hammer_plugins(["pulp-cli"]) == []


@pytest.mark.parametrize("flavor,enabled", [("satellite", True), ("katello", False)])
def test_pulp_cli_flavor_default(flavor, enabled):
    path = ROOT_DIR / "src" / "vars" / "flavors" / f"{flavor}.yml"
    flavor_vars = yaml.safe_load(path.read_text())
    assert ("pulp-cli" in flavor_vars["flavor_features"]) is enabled


def test_pulp_cli_deploy_feature_gate():
    path = ROOT_DIR / "src" / "playbooks" / "deploy" / "deploy.yaml"
    playbook = yaml.safe_load(path.read_text())
    role = next(role for role in playbook[0]["roles"] if role["role"] == "pulp_cli")
    assert role["when"] == ["enabled_features | has_feature('pulp-cli')"]
