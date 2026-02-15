"""Implementation of explicit-volume-mode rule."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable

_VOLUME_PATTERN = re.compile(r'^[^:]+:[^:]+:(rw|ro)(?:,[zZ])?$')


class ExplicitVolumeModeRule(AnsibleLintRule):
    """Volume mounts must specify explicit :rw or :ro mode."""

    id = "explicit-volume-mode"
    description = "Volume mounts must explicitly specify :rw or :ro mode, to ease auditing of access control."
    severity = "HIGH"
    tags = ["idiom"]
    version_added = "custom"

    def matchtask(self, task: dict[str, Any], file: Lintable | None = None) -> bool | str:
        """Return a match if any volume mount lacks explicit mode."""
        action = task.get("action", {})
        if action.get("__ansible_module__") != "containers.podman.podman_container":
            return False

        for volume_key in ("volume", "volumes"):
            volume_data = action.get(volume_key)
            if not volume_data:
                continue

            if isinstance(volume_data, str):
                specs = [volume_data]
            elif isinstance(volume_data, list):
                specs = [s for s in volume_data if isinstance(s, str)]
            else:
                continue

            for spec in specs:
                if not _is_valid(spec):
                    return f"Volume mount '{spec}' missing explicit mode (:rw or :ro)"

        return False


def _is_valid(spec: str) -> bool:
    if "{{" in spec:
        return True
    return bool(_VOLUME_PATTERN.match(spec.strip().strip("'\"")))
