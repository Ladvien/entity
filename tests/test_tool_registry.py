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


@pytest.mark.asyncio
async def test_discover_tools_by_intent() -> None:
    registry = ToolRegistry()
    await registry.add("alpha", AlphaTool())
    await registry.add("beta", BetaTool())

    found = registry.discover(intent="calc")
    assert len(found) == 1
    assert found[0][0] == "alpha"
    assert isinstance(found[0][1], AlphaTool)

    found_ci = registry.discover(intent="CALC")
    assert len(found_ci) == 1
    assert found_ci[0][0] == "alpha"
