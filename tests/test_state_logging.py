from __future__ import annotations

import asyncio
from datetime import datetime

from pipeline import PluginRegistry, PromptPlugin, SystemRegistries, ToolRegistry
from pipeline.pipeline import execute_pipeline
from pipeline.stages import PipelineStage
from entity.core.state import ConversationEntry, PipelineState

from entity.core.resources.container import ResourceContainer
from entity.core.state_logger import LogReplayer, StateLogger


def _make_state(pid: str) -> PipelineState:
    return PipelineState(
        conversation=[
            ConversationEntry(
                content="hi",
                role="user",
                timestamp=datetime.now(),
            )
        ],
        pipeline_id=pid,
    )


def test_logger_and_replay(tmp_path):
    log_file = tmp_path / "log.jsonl"
    logger = StateLogger(log_file)

    state = _make_state("123")
    logger.log(state, PipelineStage.PARSE)
    state.prompt = "next"
    logger.log(state, PipelineStage.DO)
    logger.close()

    replayer = LogReplayer(log_file)
    transitions = list(replayer.transitions())

    assert len(transitions) == 2
    assert transitions[0].pipeline_id == "123"
    assert transitions[0].stage == "parse"
    assert transitions[1].stage == "do"


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.OUTPUT]

    async def _execute_impl(self, context):
        context.set_response("ok")


def test_execute_pipeline_logs_states(tmp_path):
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.OUTPUT)
    )
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)

    log_file = tmp_path / "run.jsonl"
    logger = StateLogger(log_file)

    result = asyncio.run(execute_pipeline("hi", capabilities, state_logger=logger))
    logger.close()
    assert result == "ok"

    transitions = list(LogReplayer(log_file).transitions())
    stages = [t.stage for t in transitions]
    assert stages[0] == "parse"
    assert "output" in stages[-1]
