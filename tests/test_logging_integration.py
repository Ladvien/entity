import asyncio
import json
import types

import pytest

from entity.core.context import PluginContext
from entity.core.state import PipelineState
from entity.core.plugins import Plugin, ResourcePlugin
from entity.core.stages import PipelineStage
from entity.resources.logging import LoggingResource


class DummyPlugin(Plugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context: PluginContext) -> str:
        return "ok"


class DummyResource(ResourcePlugin):
    infrastructure_dependencies: list[str] = []
    resource_category = "test"

    async def do(self) -> str:
        async def _inner() -> str:
            return "done"

        return await self._track_operation(operation="do", func=_inner)


@pytest.mark.asyncio
async def test_plugin_logging(tmp_path):
    log_file = tmp_path / "plugin.jsonl"
    logger = LoggingResource(
        {"outputs": [{"type": "structured_file", "path": str(log_file)}]}
    )
    await logger.initialize()
    plugin = DummyPlugin({})
    plugin.logging = logger
    registries = types.SimpleNamespace(
        resources=types.SimpleNamespace(get=lambda _n: None),
        tools=types.SimpleNamespace(),
        plugins=None,
        validators=None,
    )
    state = PipelineState(conversation=[], pipeline_id="123")
    context = PluginContext(state, registries)
    context.set_current_stage(PipelineStage.THINK)

    await plugin.execute(context)
    await logger.shutdown()
    with open(log_file, "r", encoding="utf-8") as handle:
        entries = [json.loads(line) for line in handle]

    messages = [e["message"] for e in entries]
    assert "Plugin execution started" in messages
    assert "Plugin execution succeeded" in messages


@pytest.mark.asyncio
async def test_resource_logging(tmp_path):
    log_file = tmp_path / "resource.jsonl"
    logger = LoggingResource(
        {"outputs": [{"type": "structured_file", "path": str(log_file)}]}
    )
    await logger.initialize()
    resource = DummyResource({})
    resource.logging = logger

    await resource.do()
    await logger.shutdown()
    with open(log_file, "r", encoding="utf-8") as handle:
        entries = [json.loads(line) for line in handle]

    messages = [e["message"] for e in entries]
    assert "do started" in messages
    assert "do succeeded" in messages
