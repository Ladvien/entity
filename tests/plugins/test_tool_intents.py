import pytest

from entity.core.registries import ToolRegistry
from entity.core.plugins import ToolPlugin
from entity.core.stages import PipelineStage


class HelloTool(ToolPlugin):
    stages = [PipelineStage.DO]
    intents = ["greeting"]

    async def execute_function(self, params):
        return "hello"


class EchoTool(ToolPlugin):
    stages = [PipelineStage.DO]
    intents = ["echo", "greeting"]

    async def execute_function(self, params):
        return params.get("text", "")


@pytest.mark.asyncio
async def test_discover_by_intent() -> None:
    registry = ToolRegistry()
    await registry.add("hello", HelloTool())
    await registry.add("echo", EchoTool())

    greeting_tools = [name for name, _ in registry.discover(intent="greeting")]
    assert greeting_tools == ["hello", "echo"]

    echo_tools = [name for name, _ in registry.discover(intent="echo")]
    assert echo_tools == ["echo"]
