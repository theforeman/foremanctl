import pytest
import yaml

ROLE_MAP = {
    "iop-ingress": "iop_ingress",
    "iop-inventory": "iop_inventory",
    "iop-advisor": "iop_advisor",
}


def _load_role_image(role_name):
    with open(f"src/roles/{role_name}/defaults/main.yaml") as f:
        defaults = yaml.safe_load(f)
    image = defaults[f"{role_name}_container_image"]
    tag = defaults[f"{role_name}_container_tag"]
    return f"{image}:{tag}"


@pytest.fixture(scope="module")
def iop_image():
    cache = {}

    def _get(name):
        if name not in cache:
            cache[name] = _load_role_image(ROLE_MAP[name])
        return cache[name]

    return _get
