import asyncio

from fastapi.testclient import TestClient
from plugins.builtin.adapters import WebSocketAdapter

<<<<<<< HEAD
from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      PromptPlugin, ResourceContainer, SystemRegistries,
                      ToolRegistry)
=======
from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
>>>>>>> 842b365f2ee0307cf77e24d7bdb710602bc576a8


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter():
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DO))
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    return WebSocketAdapter(manager)


def test_websocket_adapter_basic():
    adapter = make_adapter()
    client = TestClient(adapter.app)

    with client.websocket_connect("/") as ws:
        ws.send_text("hello")
        data = ws.receive_json()
        assert data == {"msg": "hello"}
    client.close()
