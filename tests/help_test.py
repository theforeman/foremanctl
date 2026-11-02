import subprocess

import pytest

PERSISTED_EPILOG = "Parameters marked as (persisted) can be reset by --reset-<parameter-name>."


@pytest.mark.parametrize("command", ["auth-bundle", "backup", "features", "migrate", "restore"])
def test_non_persisted_commands_do_not_show_persisted_epilog(command):
   result = subprocess.run(
       ["./foremanctl", command, "--help"],
       capture_output=True,
       text=True,
   )
   assert result.returncode == 0
   assert PERSISTED_EPILOG not in result.stdout
   assert "(persisted)" not in result.stdout


@pytest.mark.parametrize("command", ["checks", "deploy", "deploy-proxy", "health"])
def test_deploy_help_still_shows_persisted_epilog(command):
   result = subprocess.run(
       ["./foremanctl", command, "--help"],
       capture_output=True,
       text=True,
   )
   assert result.returncode == 0
   assert PERSISTED_EPILOG in result.stdout
   assert "(persisted)" in result.stdout


@pytest.mark.parametrize("command", ["deploy", "deploy-proxy"])
def test_tftp_options_are_available_on_both_deployment_paths(command):
   result = subprocess.run(
       ["./foremanctl", command, "--help"],
       capture_output=True,
       text=True,
   )
   assert result.returncode == 0
   assert "--tftp-root" in result.stdout
   assert "--tftp-servername" in result.stdout
