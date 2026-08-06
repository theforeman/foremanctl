"""Implementation of role-scoped-variables rule."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jinja2 import Environment, TemplateSyntaxError
from jinja2.meta import find_undeclared_variables

from ansiblelint.rules import AnsibleLintRule

if TYPE_CHECKING:
    from ansiblelint.file_utils import Lintable

_JINJA_ENV = Environment()

ANSIBLE_BUILTINS = {
    "item",
    "omit",
    "true",
    "false",
    "none",
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
    "lookup",
    "query",
    "q",
    "now",
    "undef",
}

ALLOWED_GLOBALS = {
    "obsah_state_path",
}

_IMPLICIT_JINJA_KEYS = frozenset({
    "when",
    "failed_when",
    "changed_when",
    "until",
})

def _extract_jinja_vars(text: str, implicit: bool = False) -> set[str]:
    """Extract variable references from a string containing Jinja2."""
    variables: set[str] = set()
    if implicit:
        try:
            ast = _JINJA_ENV.parse("{{ " + text + " }}")
            variables.update(find_undeclared_variables(ast))
        except TemplateSyntaxError:
            pass
        return variables

    if "{{" not in text and "{%" not in text:
        return variables

    try:
        ast = _JINJA_ENV.parse(text)
        variables.update(find_undeclared_variables(ast))
    except TemplateSyntaxError:
        pass
    return variables


def _walk_values(data: Any, implicit: bool = False) -> set[str]:
    """Recursively extract Jinja variable references from a data structure."""
    variables: set[str] = set()
    if isinstance(data, str):
        variables.update(_extract_jinja_vars(data, implicit=implicit))
    elif isinstance(data, list):
        for entry in data:
            variables.update(_walk_values(entry, implicit=implicit))
    elif isinstance(data, dict):
        for value in data.values():
            variables.update(_walk_values(value, implicit=implicit))
    return variables


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

    def matchtask(self, task: dict[str, Any], file: Lintable | None = None) -> bool | str:
        """Flag tasks that reference variables not scoped to their role."""
        if not file or not file.role:
            return False

        role_prefix = file.role + "_"
        variables: set[str] = set()

        action = task.get("action", {})
        for key, value in action.items():
            if key.startswith("__"):
                continue
            variables.update(_walk_values(value))

        for key in _IMPLICIT_JINJA_KEYS:
            value = task.get(key)
            if value is not None:
                if isinstance(value, list):
                    for entry in value:
                        if isinstance(entry, str):
                            variables.update(_walk_values(entry, implicit=True))
                elif isinstance(value, str):
                    variables.update(_walk_values(value, implicit=True))

        task_vars = task.get("vars", {})
        task_var_keys: set[str] = set()
        if isinstance(task_vars, dict):
            task_var_keys = set(task_vars.keys())
            for value in task_vars.values():
                variables.update(_walk_values(value))

        for key in ("loop", "environment", "retries", "delay"):
            value = task.get(key)
            if value is not None:
                variables.update(_walk_values(value))

        loop_control = task.get("loop_control", {})
        if isinstance(loop_control, dict):
            custom_loop_var = loop_control.get("loop_var")
            if isinstance(custom_loop_var, str):
                variables.discard(custom_loop_var)

        variables -= task_var_keys

        violations = sorted(v for v in variables if not _is_allowed(v, role_prefix))

        if violations:
            return (
                f"Variables not scoped to role '{file.role}': "
                + ", ".join(violations)
            )
        return False
