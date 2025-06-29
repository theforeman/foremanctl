import pytest
import subprocess
import os

SCRIPT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "src", "roles", "hostname_check", "files", "foreman-hostname-check"
    )
)

if not os.path.exists(SCRIPT_PATH):
    pytest.fail(f"Hostname check script not found at: {SCRIPT_PATH}")


def run_script(args=None):
    cmd = [SCRIPT_PATH]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )
    return result


def test_hostname_check_passes_on_valid_host():
    result = run_script()
    assert result.returncode == 0
    assert "[OK]" in result.stdout
    assert "Hostname validation succeeded" in result.stdout


@pytest.mark.skip(reason="requires mocking hostname output")
def test_hostname_check_fails_on_localhost():
    pass
