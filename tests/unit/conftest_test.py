from types import SimpleNamespace

from tests.conftest import UserParameters


def test_all_available_features_uses_complete_catalog(tmp_path):
    source_dir = tmp_path / 'src'
    source_dir.mkdir()
    overlays_dir = source_dir / 'features.d'
    overlays_dir.mkdir()
    (source_dir / 'features.yaml').write_text(
        'server-only:\n'
        '  flavors:\n'
        '    - katello\n'
    )
    (overlays_dir / 'content.yaml').write_text(
        'proxy-only:\n'
        '  flavors:\n'
        '    - foreman-proxy-content\n'
    )

    user_parameters = UserParameters(SimpleNamespace(rootdir=tmp_path))

    assert user_parameters.all_available_features == {'server-only', 'proxy-only'}
