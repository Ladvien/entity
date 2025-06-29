import asyncio
import httpx
from fastapi.testclient import TestClient

<<<<<<< HEAD

=======
>>>>>>> 346eeb378c849154625acfe74df5c293057eca04
from pipeline import (
    HTTPAdapter,
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)


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
