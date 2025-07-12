import asyncio

from entity.core.agent import Agent
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


def test_plugin_lifecycle():
    ag = Agent()
    plugin = LifecyclePlugin({})
    asyncio.run(ag.builder.add_plugin(plugin))
    asyncio.run(ag.builder.build_runtime())

    asyncio.run(plugin.execute(object()))
    assert plugin.initialized
    assert plugin.executed

    ag.builder.shutdown()
    assert plugin.closed
