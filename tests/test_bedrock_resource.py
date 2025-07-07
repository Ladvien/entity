from __future__ import annotations

import asyncio
import json

from plugins.builtin.resources.llm.unified import UnifiedLLMResource


async def run_generate(server, handler):
    base_url = f"http://localhost:{server.server_port}"
    resource = UnifiedLLMResource(
        {"provider": "bedrock", "model_id": "mi", "endpoint_url": base_url}
    )
    handler.response = {"outputText": "hi"}
    result = await resource._providers[0].generate("hello")
    body = json.loads(handler.request_body.decode())
    assert body == {"prompt": "hello"}
    assert handler.request_path == "/model/mi/invoke"
    return result


def test_generate_sends_prompt_and_returns_content(mock_llm_server):
    server, handler = mock_llm_server
    result = asyncio.run(run_generate(server, handler))
    assert result.content == "hi"
