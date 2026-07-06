"""Implementation of use-has-feature-filter rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

_ANTI_PATTERN = "in enabled_features"


def _check_when(when: Any) -> str | None:
    """Return the offending condition string, or None."""
    if isinstance(when, str):
        when = [when]
    if not isinstance(when, list):
        return None
    for condition in when:
        if isinstance(condition, str) and _ANTI_PATTERN in condition and "has_feature" not in condition:
            return condition
    return None


class UseHasFeatureFilterRule(AnsibleLintRule):
    """Use the has_feature filter instead of 'in enabled_features' checks."""

    id = "use-has-feature-filter"
    description = (
        "Feature checks must use the has_feature filter "
        "(e.g. enabled_features | has_feature('x')) "
        "instead of raw 'in enabled_features' tests, "
        "which bypass prefix and transitive-dependency matching."
    )
    severity = "HIGH"
    tags = ["idiom"]
    version_added = "custom"

    def matchtask(self, task: dict[str, Any], file: Lintable | None = None) -> bool | str:
        """Flag task-level when clauses that use 'in enabled_features'."""
        condition = _check_when(task.get("when"))
        if condition:
            return f"Use 'enabled_features | has_feature(...)' instead of '{condition}'"
        return False

    def matchplay(self, file: Lintable, data: dict[str, Any]) -> list[MatchError]:
        """Flag role-level when clauses that use 'in enabled_features'."""
        results: list[MatchError] = []

        for role_entry in data.get("roles", []):
            if not isinstance(role_entry, dict):
                continue
            condition = _check_when(role_entry.get("when"))
            if condition:
                results.append(
                    self.create_matcherror(
                        message=f"Use 'enabled_features | has_feature(...)' instead of '{condition}'",
                        filename=file,
                        tag="use-has-feature-filter",
                    ),
                )

        return results

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Flag variable values that use 'in enabled_features'."""
        results: list[MatchError] = super().matchyaml(file)

        if str(file.kind) != "vars" or not file.data:
            return results

        meta_data = parse_yaml_from_file(str(file.path))
        if not isinstance(meta_data, dict):
            return results

        for key, value in meta_data.items():
            if not isinstance(value, str):
                continue
            if _ANTI_PATTERN in value and "has_feature" not in value:
                results.append(
                    self.create_matcherror(
                        message=f"Variable '{key}' uses 'in enabled_features'. Use the has_feature filter instead.",
                        filename=file,
                        tag="use-has-feature-filter",
                        data=key,
                    ),
                )

        return results
