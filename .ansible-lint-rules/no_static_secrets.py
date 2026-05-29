"""Implementation of var-secrets rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.text import has_jinja
from ansiblelint.utils import parse_yaml_from_file

if TYPE_CHECKING:
    from ansiblelint.errors import MatchError
    from ansiblelint.file_utils import Lintable

SECRET_SUFFIXES = (
    "_password",
    "_passwd",
    "_secret",
    "_token",
)


class NoStaticSecretsRule(AnsibleLintRule):
    """Variables that look like secrets must not have static default values."""

    id = "var-secrets"
    severity = "HIGH"
    tags = ["security"]
    version_added = "custom"

    _ids = {
        "var-secrets[no-static]": "Secret variables must use Jinja expressions, not static strings.",
    }

    @staticmethod
    def _looks_like_secret(name: str) -> bool:
        return any(name.endswith(suffix) for suffix in SECRET_SUFFIXES)

    def matchyaml(self, file: Lintable) -> list[MatchError]:
        """Flag secret-looking variables with static string values."""
        results: list[MatchError] = []

        if str(file.kind) != "vars" or not file.data:
            return results

        meta_data = parse_yaml_from_file(str(file.path))
        if not isinstance(meta_data, dict):
            return results

        for key, value in meta_data.items():
            if not self._looks_like_secret(str(key)):
                continue
            if isinstance(value, str) and not has_jinja(value):
                results.append(
                    self.create_matcherror(
                        message=f"Secret variable '{key}' has a static value. Use a Jinja expression instead.",
                        filename=file,
                        tag="var-secrets[no-static]",
                        data=key,
                    ),
                )

        return results
