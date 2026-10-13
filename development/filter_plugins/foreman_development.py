from __future__ import annotations

from ansible.errors import AnsibleFilterError


def resolve_foreman_development_plugins(plugins, registry):
    """Return requested plugins and their dependencies, dependencies first."""
    resolved = []
    visited = set()
    visiting = []

    def visit(plugin):
        if plugin not in registry:
            raise AnsibleFilterError(f"Unknown Foreman development plugin: {plugin}")

        if plugin in visited:
            return
        if plugin in visiting:
            cycle = visiting[visiting.index(plugin):] + [plugin]
            raise AnsibleFilterError(
                "Circular Foreman development plugin dependencies: " + " -> ".join(cycle)
            )

        visiting.append(plugin)
        for dependency in registry[plugin].get("dependencies", []):
            visit(dependency)
        visiting.pop()

        visited.add(plugin)
        resolved.append(plugin)

    for plugin in plugins:
        visit(plugin)

    return resolved


class FilterModule:
    def filters(self):
        return {"resolve_foreman_development_plugins": resolve_foreman_development_plugins}
