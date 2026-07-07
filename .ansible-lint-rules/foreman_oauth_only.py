"""Implementation of foreman-oauth-only rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable


class ForemanOAuthOnlyRule(AnsibleLintRule):
    """Foreman API tasks must authenticate with OAuth, not username/password."""

    id = "foreman-oauth-only"
    description = (
        "Tasks using theforeman.foreman.* modules must use "
        "oauth1_consumer_key/oauth1_consumer_secret instead of username/password."
    )
    severity = "HIGH"
    tags = ["security"]
    version_added = "custom"

    def matchtask(self, task: dict[str, Any], file: Lintable | None = None) -> bool | str:
        """Flag theforeman.foreman tasks that use password authentication."""
        action = task.get("action", {})
        module = action.get("__ansible_module__", "")

        if not module.startswith("theforeman.foreman."):
            return False

        if "username" in action or "password" in action:
            return (
                "Use oauth1_consumer_key/oauth1_consumer_secret "
                "instead of username/password for Foreman API authentication"
            )

        return False
