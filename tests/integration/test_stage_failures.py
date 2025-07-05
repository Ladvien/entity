import asyncio
from pathlib import Path

import pytest

from pipeline import PipelineStage, execute_pipeline
from registry import PluginRegistry, ResourceRegistry, SystemRegistries, ToolRegistry


class RespondPlugin:
    stages = [PipelineStage.DO]

    async def execute(self, context):
        context.set_response("ok")


def make_failing_plugin(stage: PipelineStage):
    class FailingPlugin:
        stages = [stage]

        async def execute(self, context):
            if not context.metadata.get("failed"):
                context.metadata["failed"] = True
                raise RuntimeError("boom")
            context.set_stage_result(str(stage), True)

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
        plugins.register_plugin_for_stage(make_failing_plugin(stage), stage)
        plugins.register_plugin_for_stage(RespondPlugin(), PipelineStage.DO)
        registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
        try:
            await execute_pipeline("hi", registries, state_file=str(state_file))
        except RuntimeError:
            pass
        result = await execute_pipeline("hi", registries, state_file=str(state_file))
        return result.get("message", "")

    assert asyncio.run(run()) == "ok"
