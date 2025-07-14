import pytest

from entity.core.registries import ToolRegistry
from entity.core.plugins import ToolPlugin
from entity.core.stages import PipelineStage


class AlphaTool(ToolPlugin):
    stages = [PipelineStage.DO]
    intents = ["calc"]

    async def execute_function(self, params):
        return "a"


class BetaTool(ToolPlugin):
    stages = [PipelineStage.DO]
    intents = ["text"]

    async def execute_function(self, params):
        return "b"


class MultiTool(ToolPlugin):
    stages = [PipelineStage.DO]
    intents = ["calc", "text"]

    async def execute_function(self, params):
        return "c"


@pytest.mark.asyncio
async def test_discover_tools_by_intent() -> None:
    registry = ToolRegistry()
    await registry.add("alpha", AlphaTool())
    await registry.add("beta", BetaTool())
    await registry.add("multi", MultiTool())

    found = registry.discover(intent="calc")
    assert [name for name, _ in found] == ["alpha"]
    assert isinstance(found[0][1], AlphaTool)

    found_ci = registry.discover(intent="CALC")
    assert [name for name, _ in found_ci] == ["alpha"]

    found_text = registry.discover(intent="text")
    assert {name for name, _ in found_text} == {"beta", "multi"}


@pytest.mark.asyncio
async def test_discover_when_only_multi_intent_tool_registered() -> None:
    registry = ToolRegistry()
    await registry.add("multi", MultiTool())

    found = registry.discover(intent="calc")
    assert [name for name, _ in found] == ["multi"]
