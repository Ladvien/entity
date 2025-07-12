import asyncio

from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.resources.memory import Memory
from entity.worker.pipeline_worker import PipelineWorker
from pipeline.base_plugins import PromptPlugin
from pipeline.stages import PipelineStage


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):  # pragma: no cover - trivial
        context.set_response("ok")


async def build_worker() -> PipelineWorker:
    resources = ResourceContainer()
    await resources.add("memory", Memory())
    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.OUTPUT)
    regs = SystemRegistries(resources, ToolRegistry(), plugins)
    return PipelineWorker(regs)


def test_worker_keeps_no_state_between_calls():
    async def run():
        worker = await build_worker()
        memory = worker.registries.resources.get("memory")
        await worker.execute_pipeline("1", "hello")
        convo1 = await memory.load_conversation("1")
        assert convo1 and convo1[-1].content == "hello"
        assert vars(worker) == {"registries": worker.registries}

        await worker.execute_pipeline("2", "bye")
        convo2 = await memory.load_conversation("2")
        assert convo2 and convo2[-1].content == "bye"
        assert vars(worker) == {"registries": worker.registries}

    asyncio.run(run())
