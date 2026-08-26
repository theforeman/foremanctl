import subprocess
from pathlib import Path

import pytest
import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_FILE = (
    REPOSITORY_ROOT / ".var/lib/foremanctl/parameters.yaml"
)


@pytest.fixture
def air_gapped():
    if not PARAMETERS_FILE.exists():
        pytest.skip("foremanctl parameters file not found")

    try:
        parameters = yaml.safe_load(PARAMETERS_FILE.read_text()) or {}
    except yaml.YAMLError as error:
        pytest.fail(f"Failed to parse parameters.yaml: {error}")

    if parameters.get("air_gapped") is not True:
        pytest.skip("Not running in air-gapped mode")

    return parameters


def test_air_gapped_image_policy_never(server, air_gapped):
    """Verify generated image units have Policy=never in air-gapped mode."""
    result = server.run(
        "find /etc/containers/systemd "
        "-maxdepth 1 -type f -name '*.image' -print"
    )

    assert not result.failed

    image_files = result.stdout.splitlines()
    assert image_files, "No generated image units found"

    for image_file in image_files:
        lines = server.file(image_file).content_string.splitlines()

        assert "Policy=never" in lines, (
            f"{image_file} does not contain Policy=never"
        )
        assert "Policy=missing" not in lines


@pytest.mark.feature("katello")
def test_subscription_connection_disabled(foremanapi, air_gapped):
    """Verify subscription_connection_enabled is disabled in air-gapped mode."""
    settings = foremanapi.list(
        "settings",
        search="name=subscription_connection_enabled",
    )

    assert len(settings) == 1
    assert settings[0]["value"] is False
    assert settings[0]["readonly"] is True


def test_pull_images_blocked_in_air_gapped_mode(air_gapped):
    """Verify foremanctl pull-images fails in air-gapped mode."""
    result = subprocess.run(
        [str(REPOSITORY_ROOT / "foremanctl"), "pull-images"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )

    output = f"{result.stdout}\n{result.stderr}".lower()

    assert result.returncode != 0
    assert "image pulling is disabled in air-gapped mode" in output
