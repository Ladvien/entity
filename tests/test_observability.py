import asyncio
import time

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)
from pipeline.resources import ResourceContainer


class TimedPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        await asyncio.sleep(0.05)
        context.set_response("ok")


def make_registries():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(TimedPlugin({}), PipelineStage.DELIVER)
    )
    return SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)


def test_metrics_overhead():
    registries = make_registries()
    start = time.time()
    result, metrics = asyncio.run(
        execute_pipeline("hi", registries, return_metrics=True)
    )
    duration = time.time() - start
    plugin_key = f"{PipelineStage.DELIVER}:TimedPlugin"
    recorded = metrics.plugin_durations[plugin_key][0]
    assert result == "ok"
    assert recorded >= 0.05
    assert duration - recorded < 0.05
