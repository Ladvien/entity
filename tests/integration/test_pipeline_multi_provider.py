import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from pipeline import AgentBuilder, PipelineStage
from pipeline.base_plugins import BasePlugin
from plugins.builtin.resources.llm.unified import UnifiedLLMResource


class FailHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # pragma: no cover - simple failing server
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(500)
        self.end_headers()


class LLMResponder(BasePlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        response = await context.ask_llm(context.message)
        context.set_response(response)


@pytest.mark.integration
def test_pipeline_llm_failover():
    server = HTTPServer(("localhost", 0), FailHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://localhost:{server.server_port}"
    config = {
        "provider": "openai",
        "fallback": "echo",
        "api_key": "key",
        "model": "test",
        "base_url": base_url,
    }
    try:
        builder = AgentBuilder()
        builder.add_plugin(LLMResponder({}))
        builder.resource_registry.register("llm", UnifiedLLMResource, config)
        runtime = builder.build_runtime()
        result = asyncio.run(runtime.run_pipeline("hi"))
        assert result == "hi"
    finally:
        server.shutdown()
        thread.join()
