import asyncio
import json
from pathlib import Path

import httpx

from entity.core.resources.container import ResourceContainer
from entity.core.runtime import _AgentRuntime
from pipeline import (
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from plugins.builtin.adapters import DashboardAdapter


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter(tmp_path: Path) -> DashboardAdapter:
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DELIVER)
    capabilities = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    runtime = _AgentRuntime(capabilities)
    log_path = tmp_path / "state.log"
    cfg = {
        "dashboard": True,
        "state_log_path": str(log_path),
        "pipeline_config": str(Path("config/dev.yaml")),
    }
    return DashboardAdapter(runtime, cfg), log_path


def write_log(path: Path) -> None:
    entry = {
        "timestamp": "t",
        "pipeline_id": "p",
        "stage": "parse",
        "state": {},
    }
    with path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def test_dashboard_routes(tmp_path):
    adapter, log_path = make_adapter(tmp_path)
    write_log(log_path)

    async def _requests():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/dashboard")
            assert resp.status_code == 200
            resp = await client.get("/dashboard/transitions")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list) and len(data) == 1

    asyncio.run(_requests())
