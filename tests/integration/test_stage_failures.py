import asyncio
from datetime import datetime
from pathlib import Path

import pytest
from pipeline import PipelineStage, execute_pipeline
from pipeline.base_plugins import BasePlugin
from pipeline.pipeline import generate_pipeline_id
from pipeline.resources import ResourceContainer
from pipeline.state import ConversationEntry, MetricsCollector, PipelineState
from registry import PluginRegistry, SystemRegistries, ToolRegistry

from entity.core.state_logger import LogReplayer, StateLogger


class RespondPlugin(BasePlugin):
    stages = [PipelineStage.DELIVER]

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
        plugins = PluginRegistry()
        await plugins.register_plugin_for_stage(make_failing_plugin(stage), stage)
        await plugins.register_plugin_for_stage(RespondPlugin(), PipelineStage.DELIVER)
        capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)

        log_file = tmp_path / "state_log.jsonl"
        logger = StateLogger(log_file)

        state = PipelineState(
            conversation=[
                ConversationEntry(content="hi", role="user", timestamp=datetime.now())
            ],
            pipeline_id=generate_pipeline_id(),
            metrics=MetricsCollector(),
        )

        await execute_pipeline("hi", capabilities, state_logger=logger, state=state)
        state.failure_info = None
        result = await execute_pipeline(
            "hi", capabilities, state_logger=logger, state=state
        )

        logger.close()
        transitions = list(LogReplayer(log_file).transitions())
        stages = [t.stage for t in transitions]
        assert "deliver" in stages[-1]

        return result.get("message", "")

    assert asyncio.run(run()) == "ok"
