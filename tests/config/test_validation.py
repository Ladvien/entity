import pytest
from entity_config.models import EntityConfig
from pipeline.config import ConfigLoader
from pydantic import ValidationError


def test_valid_config_load():
    data = {
        "server": {"host": "localhost", "port": 8000},
        "plugins": {"resources": {"a": {"type": "tests.test_initializer:A"}}},
    }
    parsed = EntityConfig.from_dict(ConfigLoader.from_dict(data))
    assert parsed.server.port == 8000


def test_invalid_config_load():
    data = {"server": {"host": "localhost", "port": "bad"}}
    with pytest.raises(ValidationError):
        EntityConfig.from_dict(ConfigLoader.from_dict(data))
