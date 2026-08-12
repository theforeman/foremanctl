"""Implementation of role-scoped-variables rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jinja2 import Environment, TemplateSyntaxError, nodes
from jinja2.meta import find_undeclared_variables

from ansiblelint.rules import AnsibleLintRule
from ansiblelint.yaml_utils import nested_items_path

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable

_JINJA_ENV = Environment()

_IMPLICIT_JINJA_KEYS = frozenset({"when", "failed_when", "changed_when", "until"})

ANSIBLE_BUILTINS = frozenset({
    "item",
    "omit",
    "inventory_hostname",
    "inventory_hostname_short",
    "inventory_dir",
    "inventory_file",
    "groups",
    "group_names",
    "hostvars",
    "play_hosts",
    "playbook_dir",
    "role_path",
    "role_name",
    "environment",
})

ALLOWED_GLOBALS = frozenset({
    "obsah_state_path",
})

_IGNORED_TASK_KEYS = ("block", "ansible.builtin.block", "ansible.legacy.block")


def _find_call_targets(ast_node: nodes.Template) -> set[str]:
    """Find names used as function calls, not variable references."""
    targets: set[str] = set()
    for call in ast_node.find_all(nodes.Call):
        if isinstance(call.node, nodes.Name):
            targets.add(call.node.name)
    return targets


def _extract_jinja_vars(text: str, *, implicit: bool = False) -> set[str]:
    """Extract variable references from a Jinja2 string, excluding function calls."""
    if implicit:
        text = "{{ " + text + " }}"
    elif "{{" not in text and "{%" not in text:
        return set()
    try:
        ast = _JINJA_ENV.parse(text)
        return find_undeclared_variables(ast) - _find_call_targets(ast)
    except TemplateSyntaxError:
        return set()


def _is_allowed(var: str, role_prefix: str) -> bool:
    """Check if a variable reference is allowed inside this role."""
    if var.startswith(role_prefix) or var.lstrip("_").startswith(role_prefix):
        return True
    if var.startswith("_"):
        return True
    if var.startswith("ansible_"):
        return True
    if var in ANSIBLE_BUILTINS:
        return True
    if var in ALLOWED_GLOBALS:
        return True
    return False


class RoleScopedVariablesRule(AnsibleLintRule):
    """Role task files must only reference role-scoped variables."""

    id = "role-scoped-variables"
    description = (
        "Variables referenced inside a role's tasks must be prefixed with "
        "the role name, be Ansible built-ins, or be on the allowed globals "
        "list. Shared variables should be mapped to role-prefixed names in "
        "the playbook that invokes the role."
    )
    severity = "MEDIUM"
    tags = ["idiom"]
    version_added = "custom"

    def matchtask(
        self, task: dict[str, Any], file: Lintable | None = None,
    ) -> bool | str:
        """Flag tasks that reference variables not scoped to their role."""
        if not file or not file.role:
            return False

        role_prefix = file.role + "_"
        variables: set[str] = set()

        local_vars: set[str] = set()
        task_vars = task.get("vars", {})
        if isinstance(task_vars, dict):
            local_vars.update(task_vars.keys())

        loop_control = task.get("loop_control", {})
        if isinstance(loop_control, dict):
            loop_var = loop_control.get("loop_var")
            if isinstance(loop_var, str):
                local_vars.add(loop_var)

        for key, value, path in nested_items_path(
            task, ignored_keys=_IGNORED_TASK_KEYS,
        ):
            if isinstance(value, str):
                implicit = key in _IMPLICIT_JINJA_KEYS or any(
                    p in _IMPLICIT_JINJA_KEYS for p in path
                )
                variables.update(_extract_jinja_vars(value, implicit=implicit))

        variables -= local_vars

        violations = sorted(
            v for v in variables if not _is_allowed(v, role_prefix)
        )

        if violations:
            return (
                f"Variables not scoped to role '{file.role}': "
                + ", ".join(violations)
            )
        return False
