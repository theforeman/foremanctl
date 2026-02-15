"""Tests for explicit-volume-mode rule."""

import pytest

RULE_ID = "explicit-volume-mode"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_explicit_volume_mode", RULE_ID)], indirect=True)
def test_missing_mode_flagged(ansible_lint_runner) -> None:
    """Volume mounts without explicit :rw or :ro produce match errors."""
    assert len(ansible_lint_runner) == 3
    for result in ansible_lint_runner:
        assert result.rule.id == RULE_ID


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_explicit_volume_mode_pass", RULE_ID)], indirect=True)
def test_valid_mode_passes(ansible_lint_runner) -> None:
    """Volume mounts with explicit :rw or :ro do not produce errors."""
    assert len(ansible_lint_runner) == 0
