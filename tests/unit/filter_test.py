import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'filter_plugins'))

from foremanctl import FEATURE_MAP
from foremanctl import asymmetric_conflicts
from foremanctl import conflicting_features


def test_no_conflicts():
    assert conflicting_features(['foreman', 'hammer']) == []


def test_detects_conflict(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['test-b']})
    monkeypatch.setitem(FEATURE_MAP, 'test-b', {'conflicts': ['test-a']})
    result = conflicting_features(['test-a', 'test-b'])
    assert len(result) == 1
    assert 'test-a conflicts with test-b' in result


def test_deduplicates_conflict_pairs(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['test-b']})
    monkeypatch.setitem(FEATURE_MAP, 'test-b', {'conflicts': ['test-a']})
    result = conflicting_features(['test-b', 'test-a'])
    assert len(result) == 1


def test_no_conflict_when_only_one_present(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['test-b']})
    monkeypatch.setitem(FEATURE_MAP, 'test-b', {'conflicts': ['test-a']})
    assert conflicting_features(['test-a', 'foreman']) == []


def test_no_asymmetric_conflicts_in_features_yaml():
    errors = asymmetric_conflicts()
    assert errors == [], f"Asymmetric conflicts found: {errors}"


def test_asymmetric_conflict_detected(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['test-b']})
    monkeypatch.setitem(FEATURE_MAP, 'test-b', {})
    errors = asymmetric_conflicts()
    assert any('test-a declares conflict with test-b' in e for e in errors)


def test_conflict_with_unknown_feature_detected(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['nonexistent']})
    errors = asymmetric_conflicts()
    assert any('unknown feature nonexistent' in e for e in errors)
