import pathlib

import pytest

from conftest import has_feature

IOP_TEST_DIR = str(pathlib.Path(__file__).parent)


def pytest_collection_modifyitems(config, items):
    if has_feature("iop"):
        return

    skip_iop = pytest.mark.skip(reason="iop not enabled")
    for item in items:
        if str(item.fspath).startswith(IOP_TEST_DIR):
            item.add_marker(skip_iop)
