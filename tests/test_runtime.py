import asyncio

import pytest

from pipeline import PipelineStage
from pipeline.base_plugins import PromptPlugin
from pipeline.resources import ResourceContainer
from pipeline.runtime import AgentRuntime
from registry.registries import PluginRegistry, SystemRegistries, ToolRegistry


class Responder(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response({"message": "ok"})


async def make_runtime():
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(Responder({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return AgentRuntime(registries)


@pytest.mark.asyncio
async def test_runtime_run_pipeline_no_attribute_error():
    runtime = await make_runtime()
    result = await runtime.run_pipeline("hi")
    assert result["message"] == "ok"
