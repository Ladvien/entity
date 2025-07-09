from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineStage,
    PipelineState,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)


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


def test_restore_replaces_state():
    state1 = make_state()
    state2 = make_state()
    state1.prompt = "changed"
    state1.restore(state2)
    assert state1.prompt == ""
    assert len(state1.conversation) == 1
