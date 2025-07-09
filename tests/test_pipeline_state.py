from datetime import datetime

from pipeline import (ConversationEntry, MetricsCollector, PipelineStage,
                      PipelineState, PromptPlugin)


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):  # pragma: no cover - simple
        context.set_response("ok")


def make_state() -> PipelineState:
    return PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="123",
        metrics=MetricsCollector(),
    )


def test_snapshot_returns_deep_copy():
    state = make_state()
    snap = state.snapshot()
    snap.conversation[0].content = "bye"
    assert state.conversation[0].content == "hi"
