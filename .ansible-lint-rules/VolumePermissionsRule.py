"""Custom ansible-lint rule for validating volume mount permissions."""
import re
from typing import Any, Dict, List

from ansiblelint.rules import AnsibleLintRule


class VolumePermissionsRule(AnsibleLintRule):
    """Volume mounts must have explicit read-write or read-only permissions."""

    id = "volume-permissions"
    description = "Volume mounts must specify explicit :rw or :ro permissions"

    # Pattern for valid volume mount: source:destination:(rw|ro)[:(z|Z)]
    volume_pattern = re.compile(r'^[^:]+:[^:]+:(rw|ro)(?::[zZ])?$')

    def matchtask(self, task: Dict[str, Any], file=None) -> List[Dict[str, Any]]:
        """Check if task contains volume mounts without explicit permissions."""
        results = []

        if "containers.podman.podman_container" in task:
            container_config = task["containers.podman.podman_container"]

            for volume_key in ["volume", "volumes"]:
                if volume_key in container_config:
                    volume_data = container_config[volume_key]

                    volume_specs = []
                    if isinstance(volume_data, str):
                        volume_specs = [volume_data]
                    elif isinstance(volume_data, list):
                        volume_specs = [spec for spec in volume_data if isinstance(spec, str)]

                    for volume_spec in volume_specs:
                        if not self._is_valid_volume(volume_spec):
                            results.append({
                                "message": f"Volume mount '{volume_spec}' missing explicit permission (:rw or :ro)",
                                "filename": str(file) if file else "unknown",
                                "linenumber": task.get("__line__", 1),
                            })

        return results

    def _is_valid_volume(self, volume_spec: str) -> bool:
        """Check if volume specification has valid permissions."""
        if "{{" in volume_spec and "}}" in volume_spec:
            return True

        volume_spec = volume_spec.strip().strip('"\'')

        return bool(self.volume_pattern.match(volume_spec))
