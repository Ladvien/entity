from fastapi.testclient import TestClient

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.adapters import WebSocketAdapter


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
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
