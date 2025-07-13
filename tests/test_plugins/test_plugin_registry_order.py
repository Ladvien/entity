import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage


class DummyPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass


@pytest.mark.asyncio
async def test_registry_preserves_stage_order():
    registry = PluginRegistry()
    a = DummyPlugin({})
    b = DummyPlugin({})
    c = DummyPlugin({})

    await registry.register_plugin_for_stage(a, PipelineStage.THINK, "a")
    await registry.register_plugin_for_stage(b, PipelineStage.THINK, "b")
    await registry.register_plugin_for_stage(c, PipelineStage.THINK, "c")

    assert registry.get_plugins_for_stage(PipelineStage.THINK) == [a, b, c]
    assert registry.list_plugins() == [a, b, c]


@pytest.mark.asyncio
async def test_list_plugins_uses_insertion_order():
    registry = PluginRegistry()
    a = DummyPlugin({})
    b = DummyPlugin({})
    c = DummyPlugin({})

    await registry.register_plugin_for_stage(a, PipelineStage.THINK, "a")
    await registry.register_plugin_for_stage(b, PipelineStage.DO, "b")
    await registry.register_plugin_for_stage(c, PipelineStage.INPUT, "c")

    assert registry.list_plugins() == [a, b, c]
