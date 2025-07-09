import asyncio
import json

from pipeline import (
    MetricsCollector,
    PipelineState,
    PluginContext,
    SystemInitializer,
    SystemRegistries,
)
from plugins.builtin.resources.llm.unified import UnifiedLLMResource


async def run_generate(server, handler):
    base_url = f"http://localhost:{server.server_port}"
    resource = UnifiedLLMResource(
        {
            "provider": "claude",
            "api_key": "key",
            "model": "claude-3",
            "base_url": base_url,
        }
    )
    handler.response = {"content": [{"text": "hi"}]}
    result = await resource.generate("hello")
    req = json.loads(handler.request_body.decode())
    assert req == {
        "model": "claude-3",
        "messages": [{"role": "user", "content": "hello"}],
    }
    assert handler.request_path == "/v1/messages"
    return result


def test_generate_sends_prompt_and_returns_text(mock_llm_server):
    server, handler = mock_llm_server
    assert asyncio.run(run_generate(server, handler)) == "hi"


def test_context_get_llm_with_provider():
    cfg = {
        "plugins": {
            "resources": {
                "llm": {
                    "type": "plugins.builtin.resources.llm.unified:UnifiedLLMResource",
                    "provider": "claude",
                    "api_key": "key",
                    "model": "claude-3",
                    "base_url": "https://api.anthropic.com",
                }
            }
        }
    }
    initializer = SystemInitializer.from_dict(cfg)
    plugin_reg, resource_reg, tool_reg = asyncio.run(initializer.initialize())
    state = PipelineState(conversation=[], pipeline_id="1", metrics=MetricsCollector())
    ctx = PluginContext(state, SystemRegistries(resource_reg, tool_reg, plugin_reg))
    assert isinstance(ctx.get_llm(), UnifiedLLMResource)
