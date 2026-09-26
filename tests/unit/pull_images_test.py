import os
import shutil

import obsah
import pytest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(TEST_DIR, '..', '..'))


def _parser(monkeypatch, data_path, state_path):
    monkeypatch.setenv('OBSAH_DATA', str(data_path))
    monkeypatch.setenv('OBSAH_STATE', str(state_path))
    monkeypatch.setenv('OBSAH_PERSIST_PARAMS', 'true')
    return obsah.obsah_argument_parser(obsah.ApplicationConfig, targets=[])


def _copy_playbooks(tmp_path):
    data_path = tmp_path / 'src'
    playbooks_path = data_path / 'playbooks'
    shutil.copytree(os.path.join(REPOSITORY_ROOT, 'src', 'playbooks'), playbooks_path)
    vendor_overrides_path = playbooks_path / '_vendor_overrides'
    if vendor_overrides_path.exists():
        shutil.rmtree(vendor_overrides_path)
    return data_path


@pytest.mark.parametrize('flavor', ['katello', 'foreman-proxy-content'])
def test_pull_images_accepts_flavor(monkeypatch, tmp_path, flavor):
    parser = _parser(monkeypatch, _copy_playbooks(tmp_path), tmp_path / 'state')

    args = parser.parse_args(['pull-images', '--flavor', flavor])

    assert args.flavor == flavor


@pytest.mark.parametrize('flavor', ['satellite', 'capsule'])
def test_pull_images_accepts_vendor_flavor(monkeypatch, tmp_path, flavor):
    data_path = _copy_playbooks(tmp_path)
    shutil.copytree(
        os.path.join(REPOSITORY_ROOT, 'vendor_overrides', 'satellite'),
        data_path / 'playbooks' / '_vendor_overrides',
    )
    parser = _parser(monkeypatch, data_path, tmp_path / 'state')

    args = parser.parse_args(['pull-images', '--flavor', flavor])

    assert args.flavor == flavor


def test_pull_images_accepts_iop_with_satellite(monkeypatch, tmp_path):
    data_path = _copy_playbooks(tmp_path)
    shutil.copytree(
        os.path.join(REPOSITORY_ROOT, 'vendor_overrides', 'satellite'),
        data_path / 'playbooks' / '_vendor_overrides',
    )
    parser = _parser(monkeypatch, data_path, tmp_path / 'state')

    args = parser.parse_args(
        ['pull-images', '--flavor', 'satellite', '--add-feature', 'iop']
    )

    assert args.flavor == 'satellite'
    assert 'iop' in args.features


def test_pull_images_uses_persisted_flavor(monkeypatch, tmp_path):
    state_path = tmp_path / 'state'
    state_path.mkdir()
    (state_path / 'parameters.yaml').write_text(
        'flavor: foreman-proxy-content\n',
        encoding='utf-8',
    )
    parser = _parser(monkeypatch, _copy_playbooks(tmp_path), state_path)

    args = parser.parse_args(['pull-images'])

    assert args.flavor == 'foreman-proxy-content'
