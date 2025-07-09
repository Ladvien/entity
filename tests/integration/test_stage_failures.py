import asyncio
from pathlib import Path

import pytest

from pipeline import PipelineStage, execute_pipeline
from pipeline.base_plugins import BasePlugin
from pipeline.resources import ResourceContainer
from registry import PluginRegistry, SystemRegistries, ToolRegistry


class RespondPlugin(BasePlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response({"message": "ok"})


def make_failing_plugin(stage: PipelineStage):
    class FailingPlugin(BasePlugin):
        stages = [stage]

        async def _execute_impl(self, context):
            if not context.get_metadata("failed"):
                context.set_metadata("failed", True)
                raise RuntimeError("boom")
            context.store(str(stage), True)

    return FailingPlugin()


@pytest.mark.integration
@pytest.mark.parametrize(
    "stage",
    [
        PipelineStage.PARSE,
        PipelineStage.THINK,
        PipelineStage.DO,
        PipelineStage.REVIEW,
        PipelineStage.DELIVER,
    ],
)
def test_pipeline_recovers_from_stage_failure(
    tmp_path: Path, stage: PipelineStage
) -> None:
    async def run() -> str:
        state_file = tmp_path / "state.json"
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(make_failing_plugin(stage), stage)
        await plugins.register_plugin_for_stage(RespondPlugin(), PipelineStage.DO)
        registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
        try:
            await execute_pipeline("hi", registries, state_file=str(state_file))
        except RuntimeError:
            pass
        result = await execute_pipeline("hi", registries, state_file=str(state_file))
        return result.get("message", "")

    assert asyncio.run(run()) == "ok"
