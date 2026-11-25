"""Make development filters available to local tool tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'filter_plugins'))
