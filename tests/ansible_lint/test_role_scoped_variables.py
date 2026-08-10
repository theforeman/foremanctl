"""Tests for role-scoped-variables rule."""

import pytest

RULE_ID = "role-scoped-variables"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_role_scoped_variables", RULE_ID)], indirect=True)
def test_unscoped_variables_flagged(ansible_lint_runner) -> None:
    """Tasks referencing variables not prefixed with the role name produce match errors."""
    assert len(ansible_lint_runner) == 4
    for result in ansible_lint_runner:
        assert result.rule.id == RULE_ID


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_role_scoped_variables_pass", RULE_ID)], indirect=True)
def test_scoped_variables_pass(ansible_lint_runner) -> None:
    """Tasks using role-prefixed, builtin, or allowed global variables pass."""
    assert len(ansible_lint_runner) == 0
