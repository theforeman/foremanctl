"""Tests for use-has-feature-filter rule."""

import pytest

RULE_ID = "use-has-feature-filter"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_has_feature_filter", RULE_ID)], indirect=True)
def test_raw_in_check_flagged(ansible_lint_runner) -> None:
    """Task when clauses using 'in enabled_features' produce match errors."""
    assert len(ansible_lint_runner) == 3
    for result in ansible_lint_runner:
        assert result.rule.id == RULE_ID


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_has_feature_filter_pass", RULE_ID)], indirect=True)
def test_has_feature_filter_passes(ansible_lint_runner) -> None:
    """Tasks using has_feature filter do not produce errors."""
    assert len(ansible_lint_runner) == 0


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/playbooks/test_has_feature_filter_roles.yml", RULE_ID)], indirect=True)
def test_role_level_when_flagged(ansible_lint_runner) -> None:
    """Role-level when clauses using 'in enabled_features' produce match errors."""
    assert len(ansible_lint_runner) == 2
    for result in ansible_lint_runner:
        assert result.rule.id == RULE_ID


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/playbooks/test_has_feature_filter_roles_pass.yml", RULE_ID)], indirect=True)
def test_role_level_has_feature_passes(ansible_lint_runner) -> None:
    """Role-level when clauses using has_feature filter do not produce errors."""
    assert len(ansible_lint_runner) == 0
