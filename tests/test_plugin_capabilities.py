import pytest

from entity.core.registries import PluginRegistry
from entity.core.plugins import Plugin
from entity.core.stages import PipelineStage


class _CapPlugin(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["memory", "llm"]

    async def _execute_impl(self, context):  # pragma: no cover - stub
        return None


@pytest.mark.asyncio
async def test_registry_tracks_capabilities() -> None:
    registry = PluginRegistry()
    plugin = _CapPlugin({})
    await registry.register_plugin_for_stage(plugin, str(PipelineStage.THINK))
    caps = registry.get_capabilities(plugin)
    assert caps is not None
    assert str(PipelineStage.THINK) in caps.supported_stages
    assert "memory" in caps.required_resources
    assert "llm" in caps.required_resources
