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


def test_input_adapter_class_stage_restricted():
    with pytest.raises(ConfigurationError):

        class BadInput(InputAdapterPlugin):
            stages = [PipelineStage.OUTPUT]

            async def _execute_impl(self, context):
                pass


def test_output_adapter_class_stage_restricted():
    with pytest.raises(ConfigurationError):

        class BadOutput(OutputAdapterPlugin):
            stages = [PipelineStage.INPUT]

            async def _execute_impl(self, context):
                pass
