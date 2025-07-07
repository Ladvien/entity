import asyncio
from datetime import datetime
from pathlib import Path

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
from pipeline.pipeline import execute_pipeline
from pipeline.resources import ResourceContainer


class RespondPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

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


def test_execute_pipeline_persists_snapshots(tmp_path: Path):
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespondPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    snap_dir = tmp_path / "snaps"
    result = asyncio.run(
        execute_pipeline("hello", registries, snapshots_dir=str(snap_dir))
    )
    assert result == "ok"
    files = list(snap_dir.iterdir())
    assert len(files) >= 5
