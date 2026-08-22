import pytest

pytestmark = pytest.mark.feature("iop")


def test_reposync_trigger_script(server):
    script = server.file("/usr/local/bin/iop-reposync-trigger.sh")
    assert script.exists
    assert script.is_file
    assert script.mode == 0o755
