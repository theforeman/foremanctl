import subprocess
import pytest
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.abspath(os.path.join(TEST_DIR, "..", "..", "src", "roles", "ipv6_check", "files", "foreman-ipv6-check"))

if not os.path.exists(SCRIPT_PATH):
    pytest.fail(f"Script not found at: {SCRIPT_PATH}")

def run_script_with_mocked_cmdline(cmdline_content):
    """Helper to mock /proc/cmdline using subprocess input."""
    return subprocess.run(
        ["bash", "-c", f'echo "{cmdline_content}" | {SCRIPT_PATH}'],
        text=True,
        capture_output=True,
        shell=False,
    )

def test_ipv6_check_passes_on_valid_cmdline():
    result = run_script_with_mocked_cmdline("quiet splash")
    assert result.returncode == 0
    assert "IPv6 check: OK" in result.stdout

def test_ipv6_check_fails_on_disabled_ipv6():
    result = run_script_with_mocked_cmdline("quiet splash ipv6.disable=1")
    assert result.returncode == 2
    assert "FAIL" in result.stdout or result.stderr
