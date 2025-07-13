import pytest

from entity.core.plugins import InputAdapterPlugin, OutputAdapterPlugin
from entity.core.plugins.base import ConfigurationError
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage


class DummyInput(InputAdapterPlugin):
    async def _execute_impl(self, context):
        pass


class DummyOutput(OutputAdapterPlugin):
    async def _execute_impl(self, context):
        pass


@pytest.mark.asyncio
async def test_input_adapter_registration_restricted():
    registry = PluginRegistry()
    plugin = DummyInput({})
    with pytest.raises(ConfigurationError):
        await registry.register_plugin_for_stage(plugin, PipelineStage.OUTPUT)


@pytest.mark.asyncio
async def test_output_adapter_registration_restricted():
    registry = PluginRegistry()
    plugin = DummyOutput({})
    with pytest.raises(ConfigurationError):
        await registry.register_plugin_for_stage(plugin, PipelineStage.INPUT)
