import time
import types
import psutil
import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage
from entity.worker.pipeline_worker import PipelineWorker


class InputCapture(Plugin):
    stages = [PipelineStage.INPUT]

    async def _execute_impl(self, context):
        await context.think("input", context.conversation()[-1].content)


class ParseLower(Plugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context):
        raw = await context.reflect("input")
        await context.think("parsed", raw.lower())


class ReverseThink(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        parsed = await context.reflect("parsed")
        await context.think("thought", parsed[::-1])


class ReviewPass(Plugin):
    stages = [PipelineStage.REVIEW]

    async def _execute_impl(self, context):
        await context.think("reviewed", await context.reflect("thought"))


class OutputFinal(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        final = await context.reflect("reviewed")
        context.say(final)


@pytest.mark.asyncio
async def test_end_to_end_flow(memory_db):
    regs = types.SimpleNamespace(
        resources={"memory": memory_db},
        tools=types.SimpleNamespace(),
        plugins=PluginRegistry(),
    )
    plugins = [InputCapture, ParseLower, ReverseThink, ReviewPass, OutputFinal]
    for plugin in plugins:
        await regs.plugins.register_plugin_for_stage(plugin({}), plugin.stages[0])

    worker = PipelineWorker(regs)
    result = await worker.execute_pipeline("pipe", "Hello", user_id="u1")
    assert result == "olleh"


@pytest.mark.asyncio
async def test_pipeline_performance_under_load(memory_db):
    regs = types.SimpleNamespace(
        resources={"memory": memory_db},
        tools=types.SimpleNamespace(),
        plugins=PluginRegistry(),
    )
    await regs.plugins.register_plugin_for_stage(OutputFinal({}), PipelineStage.OUTPUT)
    worker = PipelineWorker(regs)

    start = time.perf_counter()
    for i in range(50):
        await worker.execute_pipeline("pipe", f"msg{i}", user_id=f"u{i%5}")
    elapsed = time.perf_counter() - start
    mem_usage = psutil.Process().memory_info().rss
    assert elapsed > 0
    assert mem_usage > 0
