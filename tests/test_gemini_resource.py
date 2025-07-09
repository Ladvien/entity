import asyncio
import json

from pipeline import PipelineState, PluginContext, SystemInitializer, SystemRegistries
from plugins.builtin.resources.llm.unified import UnifiedLLMResource


async def run_generate(server, handler):
    base_url = f"http://localhost:{server.server_port}"
    resource = UnifiedLLMResource(
        {
            "provider": "gemini",
            "api_key": "key",
            "model": "gemini-pro",
            "base_url": base_url,
        }
    )
    handler.response = {"candidates": [{"content": {"parts": [{"text": "hi"}]}}]}
    result = await resource.generate("hello")
    req = json.loads(handler.request_body.decode())
    assert req == {"contents": [{"parts": [{"text": "hello"}]}]}
    assert handler.request_path == "/v1beta/models/gemini-pro:generateContent?key=key"
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
                    "provider": "gemini",
                    "api_key": "key",
                    "model": "gemini-pro",
                    "base_url": "https://generativelanguage.googleapis.com",
                }
            }
        }
    }
    initializer = SystemInitializer.from_dict(cfg)
    plugin_reg, resource_reg, tool_reg, _ = asyncio.run(initializer.initialize())
    ctx = PluginContext(state, SystemRegistries(resource_reg, tool_reg, plugin_reg))
    assert isinstance(ctx.get_llm(), UnifiedLLMResource)
