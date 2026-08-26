import pytest
import yaml


def test_air_gapped_image_policy_never(server, enabled_features):
    """Verify image units have Policy=never in air-gapped mode."""
    # Check if air-gapped mode is enabled
    try:
        with open("/var/lib/foremanctl/parameters.yaml") as f:
            parameters = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pytest.skip("parameters.yaml not found")

    if not parameters.get("air_gapped_mode", False):
        pytest.skip("Not in air-gapped mode")

    core_images = ['valkey', 'postgresql', 'foreman', 'candlepin', 'pulp']

    for image in core_images:
        image_file = server.file(f"/etc/containers/systemd/{image}.image")
        if image_file.exists:
            assert "Policy=never" in image_file.content_string, \
                f"{image}.image should have Policy=never in air-gapped mode"
            assert "Policy=missing" not in image_file.content_string, \
                f"{image}.image should not have Policy=missing in air-gapped mode"


def test_subscription_connection_disabled(server, foremanapi, enabled_features):
    """Verify subscription_connection_enabled is disabled in air-gapped mode."""
    # Check if air-gapped mode is enabled
    try:
        with open("/var/lib/foremanctl/parameters.yaml") as f:
            parameters = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pytest.skip("parameters.yaml not found")

    if not parameters.get("air_gapped_mode", False):
        pytest.skip("Not in air-gapped mode")

    if "foreman" not in enabled_features:
        pytest.skip("Foreman not enabled")

    settings = foremanapi.list(
        "settings",
        search="name=subscription_connection_enabled",
    )

    assert len(settings) == 1
    assert settings[0]["value"] is False
    assert settings[0]["readonly"] is True


def test_pull_images_blocked_in_air_gapped_mode(server):
    """Verify foremanctl pull-images fails in air-gapped mode."""
    # Check if air-gapped mode is enabled
    try:
        with open("/var/lib/foremanctl/parameters.yaml") as f:
            parameters = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pytest.skip("parameters.yaml not found")

    if not parameters.get("air_gapped_mode", False):
        pytest.skip("Not in air-gapped mode")

    result = server.run("foremanctl pull-images")

    assert result.failed
    assert "cannot run" in result.stderr.lower() or "disabled" in result.stderr.lower()
