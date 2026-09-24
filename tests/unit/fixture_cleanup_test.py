from tests.conftest import cleanup_content_view_versions


class RecordingForemanApi:
    def __init__(self, versions):
        self.versions = versions
        self.removed_from_environments = []
        self.deleted_versions = []

    def list(self, resource, params=None):
        assert resource == 'content_view_versions'
        assert params == {'content_view_id': 42}
        return list(self.versions)

    def resource_action(self, resource, action, params):
        assert resource == 'content_views'
        assert action == 'remove_from_environment'
        self.removed_from_environments.append(params)

    def delete(self, resource, version):
        assert resource == 'content_view_versions'
        self.deleted_versions.append(version['id'])
        self.versions.remove(version)


def test_cleanup_content_view_versions_with_no_published_versions():
    api = RecordingForemanApi([])

    cleanup_content_view_versions(api, {'id': 42})

    assert api.removed_from_environments == []
    assert api.deleted_versions == []


def test_cleanup_content_view_versions_removes_environments_before_versions():
    versions = [
        {'id': 1, 'environments': [{'id': 10}, {'id': 11}]},
        {'id': 2, 'environments': []},
        {'id': 3},
    ]
    api = RecordingForemanApi(versions)

    cleanup_content_view_versions(api, {'id': 42})

    assert api.removed_from_environments == [
        {'id': 42, 'environment_id': 10},
        {'id': 42, 'environment_id': 11},
    ]
    assert api.deleted_versions == [1, 2, 3]
    assert api.versions == []
