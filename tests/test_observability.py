import asyncio
import time

from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
    execute_pipeline,
)


class TimedPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        await asyncio.sleep(0.05)
        context.set_response("ok")


def make_registries():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(TimedPlugin({}), PipelineStage.DO)
    return SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)


def test_metrics_overhead():
    registries = make_registries()
    start = time.time()
    result, metrics = asyncio.run(
        execute_pipeline("hi", registries, return_metrics=True)
    )
    duration = time.time() - start
    plugin_key = f"{PipelineStage.DO}:TimedPlugin"
    recorded = metrics.plugin_durations[plugin_key][0]
    assert result == "ok"
    assert recorded >= 0.05
    assert duration - recorded < 0.05
