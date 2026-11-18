import json
import tomllib

import yaml


def test_pulp_cli_installed(server):
    assert server.run("rpm -q --whatprovides pulp-cli").succeeded
    assert server.run("pulp --version").succeeded


def test_pulp_cli_configuration(server, server_fqdn, certificates):
    config_file = server.file("/etc/pulp/cli.toml")
    assert config_file.user == "root"
    assert config_file.group == "root"
    assert config_file.mode == 0o644
    config = tomllib.loads(config_file.content_string)["cli"]
    assert config["base_url"] == f"https://{server_fqdn}"
    assert config["cert"] == certificates["client_certificate"]
    assert config["key"] == certificates["client_key"]
    assert config["verify_ssl"] is True
    assert server.run("pulp config validate --location /etc/pulp/cli.toml").succeeded


def test_pulp_cli_status(server):
    result = server.run("pulp --format json status")
    assert result.succeeded, result.stderr
    assert json.loads(result.stdout)["versions"]


def test_pulp_cli_task_list(server):
    result = server.run("pulp --format json task list --limit 1")
    assert result.succeeded, result.stderr
    assert isinstance(json.loads(result.stdout), list)


def test_pulp_cli_root_overrides(server):
    """Isolate root's overrides without modifying /root/.config/pulp/cli.toml."""
    config_home = server.check_output("mktemp -d")
    try:
        assert server.run("mkdir -p %s", f"{config_home}/pulp").succeeded
        assert server.run(
            "printf %%s %s > %s",
            '[cli]\nformat = "yaml"\n',
            f"{config_home}/pulp/cli.toml",
        ).succeeded
        result = server.run("XDG_CONFIG_HOME=%s pulp status", config_home)
        assert result.succeeded, result.stderr
        assert not result.stdout.lstrip().startswith("{")
        assert yaml.safe_load(result.stdout)["versions"]

        result = server.run("XDG_CONFIG_HOME=%s pulp --format json status", config_home)
        assert result.succeeded, result.stderr
        assert json.loads(result.stdout)["versions"]
    finally:
        server.run("rm -rf -- %s", config_home)
