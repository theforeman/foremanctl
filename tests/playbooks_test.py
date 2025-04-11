import os
import sys

import py.path
import pytest

import cli


@pytest.fixture
def fixture_dir():
    return py.path.local(__file__).realpath() / '..' / 'fixtures'


@pytest.fixture
def help_dir(fixture_dir):
    return fixture_dir / 'help'


def playbook_id(fixture_value):
    return fixture_value.name


@pytest.fixture(params=cli.ApplicationConfig.playbooks(), ids=playbook_id)
def playbook(request):
    yield request.param


def test_is_documented(playbook):
    assert playbook.help_text is not None


def test_filename_matches_directory(playbook):
    filename = os.path.splitext(os.path.basename(playbook.path))[0]
    dirname = os.path.basename(os.path.dirname(playbook.path))
    assert filename == dirname


def test_help(playbook, capsys, help_dir):
    os.system(f'./rop {playbook.name} --help')

    captured = capsys.readouterr()

    help_file = help_dir / '{}.txt'.format(playbook.name)

    if help_file.check(exists=1):
        expected = help_file.read()
        if sys.version_info >= (3, 10, 0):
            expected = expected.replace('optional arguments:', 'options:')
        if sys.version_info >= (3, 13, 0):
            expected = expected.replace('-e EXTRA_VARS,', '-e,')
        assert expected == captured.out
    else:
        help_file.write(captured.out)
        raise pytest.skip('Written help text')
