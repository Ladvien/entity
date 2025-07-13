import pytest
from pydantic import ValidationError

from entity.config.models import validate_config


def test_tool_registry_invalid():
    with pytest.raises(ValidationError):
        validate_config({"tool_registry": {"concurrency_limit": "bad"}})
