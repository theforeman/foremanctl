from unittest.mock import patch

from filter_plugins.foremanctl import conflicting_features


MOCK_FEATURES = {
    'alpha': {'description': 'Alpha feature'},
    'beta': {
        'description': 'Beta feature',
        'conflicts': ['gamma'],
    },
    'gamma': {'description': 'Gamma feature'},
    'delta': {
        'description': 'Delta feature',
        'conflicts': ['gamma'],
    },
}


@patch('filter_plugins.foremanctl.FEATURE_MAP', MOCK_FEATURES)
class TestConflictingFeatures:
    def test_no_conflicts(self):
        assert conflicting_features(['alpha', 'gamma']) == []

    def test_detects_conflict(self):
        result = conflicting_features(['beta', 'gamma'])
        assert len(result) == 1
        assert 'beta conflicts with gamma' in result

    def test_no_conflict_when_only_one_side_enabled(self):
        assert conflicting_features(['beta']) == []

    def test_deduplicates_when_declared_on_both_sides(self):
        both_declare = {
            'a': {'conflicts': ['b']},
            'b': {'conflicts': ['a']},
        }
        with patch('filter_plugins.foremanctl.FEATURE_MAP', both_declare):
            result = conflicting_features(['a', 'b'])
            assert len(result) == 1
            assert 'a conflicts with b' in result

    def test_multiple_conflicts(self):
        result = conflicting_features(['beta', 'delta', 'gamma'])
        assert len(result) == 2

    def test_empty_features(self):
        assert conflicting_features([]) == []

    def test_features_without_conflicts_key(self):
        assert conflicting_features(['alpha']) == []

    def test_conflict_detected_when_added_separately(self):
        """Simulates a previously persisted feature conflicting with a newly added one."""
        previously_persisted = ['beta']
        newly_added = ['gamma']
        enabled = previously_persisted + newly_added
        result = conflicting_features(enabled)
        assert len(result) == 1
        assert 'beta conflicts with gamma' in result
