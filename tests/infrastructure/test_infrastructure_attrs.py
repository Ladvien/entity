import pytest
from entity import infrastructure as infra


@pytest.mark.parametrize("name", infra.__all__)
def test_infrastructure_has_type(name):
    cls = getattr(infra, name)
    assert isinstance(getattr(cls, "infrastructure_type", None), str)
    assert cls.infrastructure_type
