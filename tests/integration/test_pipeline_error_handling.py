import asyncio

import pytest

from pipeline import PipelineStage, execute_pipeline
from pipeline.base_plugins import BasePlugin, FailurePlugin
from pipeline.resources import ResourceContainer
from registry import PluginRegistry, SystemRegistries, ToolRegistry


class FailingPlugin(BasePlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        raise RuntimeError("boom")


class MarkerPlugin(BasePlugin):
    stages = [PipelineStage.PARSE]

    def __init__(self, executed):
        super().__init__()
        self.executed = executed

    async def _execute_impl(self, context):
        self.executed.append("marker")


class ErrorRecorder(FailurePlugin):
    stages = [PipelineStage.ERROR]

    def __init__(self, executed):
        super().__init__()
        self.executed = executed

    async def _execute_impl(self, context):
        self.executed.append("error")


class ThinkPlugin(BasePlugin):
    stages = [PipelineStage.THINK]

    def __init__(self, executed):
        super().__init__()
        self.executed = executed

    async def _execute_impl(self, context):
        self.executed.append("think")


@pytest.mark.integration
def test_plugin_exception_triggers_error_and_halts_stage():
    executed = []

    async def run():
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(FailingPlugin({}), PipelineStage.PARSE)
        await plugins.register_plugin_for_stage(
            MarkerPlugin(executed), PipelineStage.PARSE
        )
        await plugins.register_plugin_for_stage(
            ErrorRecorder(executed), PipelineStage.ERROR
        )
        registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
        await execute_pipeline("hi", registries)

    asyncio.run(run())
    assert executed and executed[0] == "error"
    assert "marker" not in executed


@pytest.mark.integration
def test_pipeline_stops_processing_after_error():
    executed = []

    async def run():
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(FailingPlugin({}), PipelineStage.PARSE)
        await plugins.register_plugin_for_stage(
            ThinkPlugin(executed), PipelineStage.THINK
        )
        await plugins.register_plugin_for_stage(
            ErrorRecorder(executed), PipelineStage.ERROR
        )
        registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
        await execute_pipeline("hi", registries)

    asyncio.run(run())
    assert executed and executed[0] == "error"
    assert "think" not in executed
