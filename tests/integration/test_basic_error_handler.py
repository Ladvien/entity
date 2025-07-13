from datetime import datetime

import pytest

from entity.core.plugins import Plugin
from entity.core.context import PluginContext
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.state import ConversationEntry
from entity.pipeline.state import PipelineState
from entity.pipeline.pipeline import execute_pipeline
from entity.pipeline.stages import PipelineStage
from entity.resources.logging import LoggingResource
from entity.plugins.prompts.basic_error_handler import BasicErrorHandler


class FailPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> None:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_basic_error_handler(monkeypatch):
    logs = []

    async def fake_log(self, level, message, **kwargs):
        logs.append((level, message, kwargs))

    monkeypatch.setattr(LoggingResource, "log", fake_log)

    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(FailPlugin({}), PipelineStage.THINK, "fail")
    await plugins.register_plugin_for_stage(
        BasicErrorHandler({}), PipelineStage.ERROR, "handler"
    )

    logging_res = LoggingResource({})
    await logging_res.initialize()

    regs = SystemRegistries(
        resources={"logging": logging_res}, tools=ToolRegistry(), plugins=plugins
    )
    state = PipelineState(
        conversation=[ConversationEntry("hi", "user", datetime.now())],
        pipeline_id="pid",
    )

    result = await execute_pipeline("hi", regs, state=state)

    assert result["error"] == "boom"
    assert result["stage"] == "think"
    assert logs
