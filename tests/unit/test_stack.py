import pytest

from lab_runner.manifest import validate_resource


def test_owned_resource_is_accepted():
    validate_resource({'Id': 'abc', 'Config': {'Labels': {'io.prosaic.lab.owner': 'owner'}}}, 'abc', 'owner')


@pytest.mark.parametrize('resource', [
    {'Id': 'different', 'Config': {'Labels': {'io.prosaic.lab.owner': 'owner'}}},
    {'Id': 'abc', 'Config': {'Labels': {'io.prosaic.lab.owner': 'other'}}},
    {'Id': 'abc', 'Config': {}},
])
def test_foreign_or_replaced_resource_is_rejected(resource):
    with pytest.raises(ValueError, match='ownership'):
        validate_resource(resource, 'abc', 'owner')
