import asyncio

import httpx

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.adapters import HTTPAdapter


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        context.set_response({"msg": context._state.conversation[0].content})


def make_adapter():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    return HTTPAdapter(manager)


def test_http_adapter_basic():
    adapter = make_adapter()

    async def _make_request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.post("/", json={"message": "hello"})
            assert resp.status_code == 200
            assert resp.json() == {"msg": "hello"}

    asyncio.run(_make_request())
