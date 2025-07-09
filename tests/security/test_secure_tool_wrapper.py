from __future__ import annotations

import pytest
from entity.core.plugins import ToolPlugin
from pipeline.security import InputValidator, SecureToolWrapper
from pydantic import BaseModel


class EchoTool(ToolPlugin):
    name = "echo"

    class Params(BaseModel):
        text: str

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self.last_params: dict | None = None

    async def execute_function(self, params: dict) -> str:  # type: ignore[override]
        self.last_params = params
        return params["text"]


@pytest.mark.asyncio
async def test_secure_wrapper_validates_and_sanitizes():
    plugin = EchoTool({})
    validator = InputValidator(EchoTool.Params)
    secure = SecureToolWrapper(plugin, validator)

    result = await secure.execute({"text": "hello"})
    assert result == "hello"
    assert plugin.last_params == {"text": "hello"}
    assert isinstance(plugin.last_params, dict)


@pytest.mark.asyncio
async def test_secure_wrapper_rejects_sql_injection():
    plugin = EchoTool({})
    validator = InputValidator(EchoTool.Params)
    secure = SecureToolWrapper(plugin, validator)

    with pytest.raises(ValueError):
        await secure.execute({"text": "DROP TABLE users;"})
