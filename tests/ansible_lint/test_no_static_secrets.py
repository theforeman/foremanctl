"""Tests for no-static-secrets rule."""

import pytest

RULE_ID = "no-static-secrets"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_static_secrets/defaults/main.yml", RULE_ID)], indirect=True)
def test_static_secrets_flagged(ansible_lint_runner) -> None:
    """Static secret values produce match errors."""
    assert len(ansible_lint_runner) == 2
    for result in ansible_lint_runner:
        assert result.tag == "no-static-secrets"


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/roles/test_static_secrets/vars/main.yml", RULE_ID)], indirect=True)
def test_jinja_secrets_pass(ansible_lint_runner) -> None:
    """Jinja expression secrets are not flagged."""
    assert len(ansible_lint_runner) == 0


@pytest.mark.parametrize("ansible_lint_runner", [("tests/fixtures/ansible-lint/vars/secrets.yml", RULE_ID)], indirect=True)
def test_non_role_vars_checked(ansible_lint_runner) -> None:
    """Non-role vars files are also checked."""
    assert len(ansible_lint_runner) == 1
