import asyncio
from pathlib import Path

import pytest

from pipeline import PipelineStage, execute_pipeline
from pipeline.reliability.queue import PersistentQueue
from registry import PluginRegistry, ResourceRegistry, SystemRegistries, ToolRegistry


class CrashPlugin:
    stages = [PipelineStage.PARSE]

    async def execute(self, context):
        if not context.metadata.get("crashed"):
            context.metadata["crashed"] = True
            raise RuntimeError("boom")
        context.set_stage_result("parse", True)


@pytest.mark.integration
def test_pipeline_resume_after_crash(tmp_path: Path):
    async def run() -> str:
        state_file = tmp_path / "state.json"
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(CrashPlugin(), PipelineStage.PARSE)
        registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
        try:
            await execute_pipeline("hi", registries, state_file=str(state_file))
        except RuntimeError:
            pass
        result = await execute_pipeline("hi", registries, state_file=str(state_file))
        return result.get("message", "")

    assert asyncio.run(run()) != ""


def test_persistent_queue(tmp_path: Path):
    q = PersistentQueue(str(tmp_path / "q.json"))
    q.put({"a": 1})
    assert len(q) == 1
    item = q.get()
    assert item == {"a": 1}
