import pytest

pytestmark = pytest.mark.feature('foreman')


def test_foreman_organization(organization):
    assert organization


def test_foreman_initial_organization(foremanapi):
    assert foremanapi.list('organizations', search='name="Foreman CI"')


def test_foreman_initial_location(foremanapi):
    assert foremanapi.list('locations', search='name="Internet"')
