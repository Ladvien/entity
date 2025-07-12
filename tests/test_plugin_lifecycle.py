import asyncio
import pytest

from entity.core.builder import _AgentBuilder
from entity.core.plugins import Plugin
from entity.core.stages import PipelineStage


class LifecyclePlugin(Plugin):
    stages = [PipelineStage.THINK]

    def __init__(self, config=None):
        super().__init__(config or {})
        self.initialized = False
        self.executed = False
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def _execute_impl(self, context):
        self.executed = True
        return "ok"

    async def shutdown(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_plugin_lifecycle():
    builder = _AgentBuilder()
    plugin = LifecyclePlugin({})
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, builder.add_plugin, plugin)
    await loop.run_in_executor(None, builder.build_runtime)

    await plugin.execute(object())
    assert plugin.initialized
    assert plugin.executed

    await loop.run_in_executor(None, builder.shutdown)
    assert plugin.closed
