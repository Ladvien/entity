import pytest
from pydantic import ValidationError

from pipeline.config import ConfigLoader


def test_valid_config_load():
    data = {
        "server": {"host": "localhost", "port": 8000},
        "plugins": {"resources": {"a": {"type": "tests.test_initializer:A"}}},
    }
    cfg = ConfigLoader.from_dict(data)
    assert cfg["server"]["port"] == 8000


def test_invalid_config_load():
    data = {"server": {"host": "localhost", "port": "bad"}}
    with pytest.raises(ValidationError):
        ConfigLoader.from_dict(data)
