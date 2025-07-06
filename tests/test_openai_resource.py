import asyncio
import json

from plugins.builtin.resources.llm.unified import UnifiedLLMResource


async def run_generate(server, handler):
    base_url = f"http://localhost:{server.server_port}"
    resource = UnifiedLLMResource(
        {
            "provider": "openai",
            "api_key": "key",
            "model": "gpt-4",
            "base_url": base_url,
        }
    )
    handler.response = {"choices": [{"message": {"content": "hi"}}]}
    result = await resource.generate("hello")
    req = json.loads(handler.request_body.decode())
    assert req == {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "hello"}],
    }
    assert handler.request_path == "/v1/chat/completions"
    return result


def test_generate_sends_prompt_and_returns_text(mock_llm_server):
    server, handler = mock_llm_server
    assert asyncio.run(run_generate(server, handler)) == "hi"
