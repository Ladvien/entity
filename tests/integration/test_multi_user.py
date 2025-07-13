import types
import pytest

from entity.worker.pipeline_worker import PipelineWorker
from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.stages import PipelineStage


class EchoStorePlugin(Plugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        await context.remember("last", context.conversation()[-1].content)
        context.say(context.conversation()[-1].content)


@pytest.mark.asyncio
async def test_user_isolation(memory_db):
    regs = types.SimpleNamespace(
        resources={"memory": memory_db}, tools=types.SimpleNamespace()
    )
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(EchoStorePlugin({}), PipelineStage.OUTPUT)
    regs.plugins = plugins
    worker = PipelineWorker(regs)

    await worker.execute_pipeline("chat", "hello", user_id="alice")
    await worker.execute_pipeline("chat", "world", user_id="bob")

    hist_a = await memory_db.load_conversation("chat", user_id="alice")
    hist_b = await memory_db.load_conversation("chat", user_id="bob")

    assert [e.content for e in hist_a] == ["hello"]
    assert [e.content for e in hist_b] == ["world"]
    assert await memory_db.get("last", user_id="alice") == "hello"
    assert await memory_db.get("last", user_id="bob") == "world"
