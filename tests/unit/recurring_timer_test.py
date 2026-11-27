import pytest

from tests.feature.foreman.base_test import _service_is_running


@pytest.mark.parametrize(
    ("active_state", "result", "expected"),
    [
        ("active", "success", True),
        ("activating", "success", True),
        ("deactivating", "success", True),
        ("deactivating", "exit-code", False),
        ("inactive", "success", False),
    ],
)
def test_service_is_running(active_state, result, expected):
    properties = {"ActiveState": active_state, "Result": result}

    assert _service_is_running(properties) is expected
