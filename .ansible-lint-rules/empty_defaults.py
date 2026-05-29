"""Implementation of var-defaults rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable


class EmptyDefaultsRule(AnsibleLintRule):
    """Role default variables should not have empty values."""

    id = "var-defaults"
    severity = "HIGH"
    tags = ["idiom"]
    version_added = "custom"

    _ids = {
        "var-defaults[no-empty]": "Role default variables must not be null or empty strings.",
    }

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Return matches for empty defaults in role defaults files."""
        results: list[MatchError] = []

        if str(file.kind) != "vars" or not file.data:
            return results

        if not file.role or "defaults" not in file.path.parts:
            return results

        meta_data = parse_yaml_from_file(str(file.path))
        if not isinstance(meta_data, dict):
            return results

        for key, value in meta_data.items():
            if value is None or value == "":
                results.append(
                    self.create_matcherror(
                        message=f"Role default variable '{key}' has an empty value. Use `undef(hint='…')` to indicate defaults that need to be overriden.",
                        filename=file,
                        tag="var-defaults[no-empty]",
                        data=key,
                    ),
                )

        return results
