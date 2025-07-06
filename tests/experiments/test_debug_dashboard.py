from __future__ import annotations

from datetime import datetime

from experiments.debug_dashboard import LogReplayer, StateLogger
from pipeline.stages import PipelineStage
from pipeline.state import ConversationEntry, PipelineState


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
