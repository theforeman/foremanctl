from foremanctl import FEATURE_MAP
from foremanctl import conflicting_features
from foremanctl import foreman_plugins
from foremanctl import foreman_proxy_plugins
from foremanctl import hammer_plugins
from foremanctl import list_all_features
from foremanctl import unsatisfied_dependencies


def _asymmetric_conflicts():
    errors = []
    for feature, meta in FEATURE_MAP.items():
        for conflict in meta.get('conflicts', []):
            if conflict not in FEATURE_MAP:
                errors.append(f"{feature} declares conflict with unknown feature {conflict}")
            elif feature not in FEATURE_MAP.get(conflict, {}).get('conflicts', []):
                errors.append(f"{feature} declares conflict with {conflict}, but {conflict} does not declare conflict with {feature}")
    return errors


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
    errors = _asymmetric_conflicts()
    assert errors == [], f"Asymmetric conflicts found: {errors}"


def test_asymmetric_conflict_detected(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['test-b']})
    monkeypatch.setitem(FEATURE_MAP, 'test-b', {})
    errors = _asymmetric_conflicts()
    assert any('test-a declares conflict with test-b' in e for e in errors)


def test_conflict_with_unknown_feature_detected(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'conflicts': ['nonexistent']})
    errors = _asymmetric_conflicts()
    assert any('unknown feature nonexistent' in e for e in errors)


def test_list_all_features_marks_dependency_as_enabled(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {'dependencies': ['test-child']})
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {})
    output = list_all_features(['test-parent'])
    child_line = next(line for line in output.splitlines() if line.startswith('test-child'))
    assert 'enabled' in child_line


def test_unsatisfied_dependencies_none_when_nothing_removed():
    assert unsatisfied_dependencies(['foreman', 'katello'], []) == []


def test_unsatisfied_dependencies_ignores_transitive_deps():
    # httpd/valkey/dynflow/tasks are never listed explicitly; with no removals
    # requested this must not report them as missing.
    assert unsatisfied_dependencies(['foreman', 'katello', 'pulp']) == []


def test_unsatisfied_dependencies_detects_removed_dependency(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {'dependencies': ['test-child']})
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {})
    result = unsatisfied_dependencies(['test-parent'], ['test-child'])
    assert result == ["Cannot remove 'test-child' — it is required by enabled feature 'test-parent'"]


def test_unsatisfied_dependencies_detects_transitively_removed_dependency(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {'dependencies': ['test-mid']})
    monkeypatch.setitem(FEATURE_MAP, 'test-mid', {'dependencies': ['test-leaf']})
    monkeypatch.setitem(FEATURE_MAP, 'test-leaf', {})
    result = unsatisfied_dependencies(['test-parent'], ['test-leaf'])
    assert any("Cannot remove 'test-leaf'" in error for error in result)


def test_unsatisfied_dependencies_allows_unrelated_removal(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {'dependencies': ['test-child']})
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {})
    monkeypatch.setitem(FEATURE_MAP, 'test-other', {})
    assert unsatisfied_dependencies(['test-parent'], ['test-other']) == []


def test_foreman_plugins_deduplicates(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {
        'dependencies': ['test-child'],
        'foreman': {'plugin_name': 'parent_plugin'}
    })
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {
        'foreman': {'plugin_name': 'child_plugin'}
    })
    result = foreman_plugins(['test-parent', 'test-child'])
    assert result.count('child_plugin') == 1
    assert result.count('parent_plugin') == 1


def test_foreman_plugins_sorted(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-z', {'foreman': {'plugin_name': 'z_plugin'}})
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'foreman': {'plugin_name': 'a_plugin'}})
    monkeypatch.setitem(FEATURE_MAP, 'test-m', {'foreman': {'plugin_name': 'm_plugin'}})
    result = foreman_plugins(['test-z', 'test-a', 'test-m'])
    assert result == ['a_plugin', 'm_plugin', 'z_plugin']


def test_foreman_plugins_filters_none(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-with-plugin', {'foreman': {'plugin_name': 'has_plugin'}})
    monkeypatch.setitem(FEATURE_MAP, 'test-no-plugin', {})
    result = foreman_plugins(['test-with-plugin', 'test-no-plugin'])
    assert result == ['has_plugin']


def test_hammer_plugins_deduplicates(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {
        'dependencies': ['test-child'],
        'hammer': 'parent_hammer'
    })
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {
        'hammer': 'child_hammer'
    })
    result = hammer_plugins(['test-parent', 'test-child'])
    assert result.count('child_hammer') == 1
    assert result.count('parent_hammer') == 1


def test_hammer_plugins_sorted(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-z', {'hammer': 'z_hammer'})
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'hammer': 'a_hammer'})
    monkeypatch.setitem(FEATURE_MAP, 'test-m', {'hammer': 'm_hammer'})
    result = hammer_plugins(['test-z', 'test-a', 'test-m'])
    assert result == ['a_hammer', 'm_hammer', 'z_hammer']


def test_foreman_proxy_plugins_deduplicates(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-parent', {
        'dependencies': ['test-child'],
        'foreman_proxy': {'plugin_name': 'parent_proxy'}
    })
    monkeypatch.setitem(FEATURE_MAP, 'test-child', {
        'foreman_proxy': {'plugin_name': 'child_proxy'}
    })
    result = foreman_proxy_plugins(['test-parent', 'test-child'])
    assert result.count('child_proxy') == 1
    assert result.count('parent_proxy') == 1


def test_foreman_proxy_plugins_sorted(monkeypatch):
    monkeypatch.setitem(FEATURE_MAP, 'test-z', {'foreman_proxy': {'plugin_name': 'z_proxy'}})
    monkeypatch.setitem(FEATURE_MAP, 'test-a', {'foreman_proxy': {'plugin_name': 'a_proxy'}})
    monkeypatch.setitem(FEATURE_MAP, 'test-m', {'foreman_proxy': {'plugin_name': 'm_proxy'}})
    result = foreman_proxy_plugins(['test-z', 'test-a', 'test-m'])
    assert result == ['a_proxy', 'm_proxy', 'z_proxy']
