"""Run Molecule scenarios for Ansible roles under src/roles/."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES_DIR = REPO_ROOT / "src" / "roles"

pytestmark = pytest.mark.molecule


def discover_molecule_scenarios() -> list[tuple[str, str, Path]]:
    scenarios: list[tuple[str, str, Path]] = []
    if not ROLES_DIR.is_dir():
        return scenarios

    for role_dir in sorted(ROLES_DIR.iterdir()):
        if not role_dir.is_dir():
            continue
        molecule_dir = role_dir / "molecule"
        if not molecule_dir.is_dir():
            continue
        for scenario_dir in sorted(molecule_dir.iterdir()):
            if scenario_dir.is_dir() and (scenario_dir / "molecule.yml").is_file():
                scenarios.append((role_dir.name, scenario_dir.name, role_dir))
    return scenarios


def pytest_generate_tests(metafunc):
    if {"role", "scenario", "role_dir"} <= set(metafunc.fixturenames):
        params = discover_molecule_scenarios()
        metafunc.parametrize(
            ("role", "scenario", "role_dir"),
            params,
            ids=[f"{role}[{scenario}]" for role, scenario, _ in params],
        )


def test_molecule_role(role: str, scenario: str, role_dir: Path) -> None:
    role_molecule_config = role_dir / "molecule" / "config.yml"
    cmd = [sys.executable, "-m", "molecule", "test", "-s", scenario]
    if role_molecule_config.is_file():
        cmd.extend(["-c", str(role_molecule_config)])
    result = subprocess.run(
        cmd,
        cwd=role_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = "\n".join(
            part for part in (result.stdout, result.stderr) if part
        ).strip()
        pytest.fail(
            f"molecule test failed for role {role!r} scenario {scenario!r} "
            f"(exit {result.returncode})\n{output}"
        )
