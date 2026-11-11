"""Check command discovery without running playbooks or requiring deployed VMs."""

from collections import Counter
from pathlib import Path

import obsah
import pytest


@pytest.mark.parametrize("data_directory", ["src", "development"])
def test_playbook_command_names_are_unique(monkeypatch, data_directory):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("OBSAH_DATA", str(root / data_directory))
    monkeypatch.delenv("OBSAH_PLAYBOOKS", raising=False)
    counts = Counter(playbook.name for playbook in obsah.ApplicationConfig.playbooks())
    duplicates = {name: count for name, count in counts.items() if count > 1}
    assert not duplicates, f"Duplicate playbook commands in {data_directory}: {duplicates}"
