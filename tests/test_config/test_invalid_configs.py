import pytest
from pydantic import ValidationError

from entity.config.models import validate_config


def test_tool_registry_invalid():
    with pytest.raises(ValidationError):
        validate_config({"tool_registry": {"concurrency_limit": "bad"}})


def test_adapter_rate_limit_invalid():
    cfg = {
        "plugins": {
            "adapters": {"http": {"type": "x", "rate_limit": {"requests": "a"}}}
        }
    }
    with pytest.raises(ValidationError):
        validate_config(cfg)


def test_workflow_invalid():
    with pytest.raises(ValidationError):
        validate_config({"workflow": {"INPUT": "not_list"}})
