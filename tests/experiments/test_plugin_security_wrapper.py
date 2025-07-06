from __future__ import annotations

import pytest
from pydantic import BaseModel

from experiments.plugin_security import InputValidator, SecureToolWrapper
from pipeline.base_plugins import ToolPlugin


class EchoTool(ToolPlugin):
    name = "echo"

    class Params(BaseModel):
        text: str

    async def execute_function(self, params: dict) -> str:  # type: ignore[override]
        return params["text"]


@pytest.mark.asyncio
async def test_secure_wrapper_validates_and_sanitizes():
    plugin = EchoTool({})
    validator = InputValidator(EchoTool.Params)
    secure = SecureToolWrapper(plugin, validator)

    result = await secure.execute({"text": "hello"})
    assert result == "hello"


@pytest.mark.asyncio
async def test_secure_wrapper_rejects_sql_injection():
    plugin = EchoTool({})
    validator = InputValidator(EchoTool.Params)
    secure = SecureToolWrapper(plugin, validator)

    with pytest.raises(ValueError):
        await secure.execute({"text": "DROP TABLE users;"})
