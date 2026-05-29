"""Tests for var-defaults[no-empty] rule."""

import pytest

RULE_ID = "var-defaults"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_empty_defaults", RULE_ID)], indirect=True)
def test_empty_defaults_are_flagged(ansible_lint_runner) -> None:
    """Null and empty string defaults produce match errors."""
    assert len(ansible_lint_runner) == 4
    for result in ansible_lint_runner:
        assert result.tag == "var-defaults[no-empty]"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_empty_defaults/vars/main.yml", RULE_ID)], indirect=True)
def test_vars_file_not_checked(ansible_lint_runner) -> None:
    """Vars files are not checked, only defaults."""
    assert len(ansible_lint_runner) == 0
