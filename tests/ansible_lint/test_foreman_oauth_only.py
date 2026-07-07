"""Tests for foreman-oauth-only rule."""

import pytest

RULE_ID = "foreman-oauth-only"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_foreman_oauth_only", RULE_ID)], indirect=True)
def test_password_auth_flagged(ansible_lint_runner) -> None:
    """Tasks using username/password with theforeman.foreman modules produce match errors."""
    assert len(ansible_lint_runner) == 2
    for result in ansible_lint_runner:
        assert result.rule.id == RULE_ID


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_foreman_oauth_only_pass", RULE_ID)], indirect=True)
def test_oauth_auth_passes(ansible_lint_runner) -> None:
    """Tasks using OAuth or non-foreman tasks are not flagged."""
    assert len(ansible_lint_runner) == 0
