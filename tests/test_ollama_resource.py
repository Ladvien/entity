import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from plugins.builtin.resources.llm.unified import UnifiedLLMResource


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # pragma: no cover - simple server
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"response": "hi"}')


def run_server(server: HTTPServer) -> None:
    server.serve_forever()


async def run_generate() -> str:
    server = HTTPServer(("localhost", 0), Handler)
    thread = Thread(target=run_server, args=(server,), daemon=True)
    thread.start()
    base_url = f"http://localhost:{server.server_port}"
    resource = UnifiedLLMResource(
        {"provider": "ollama", "base_url": base_url, "model": "test"}
    )
    try:
        result = await resource.generate("hello")
    finally:
        server.shutdown()
        thread.join()
    return result


def test_generate_returns_text():
    assert asyncio.run(run_generate()) == "hi"
