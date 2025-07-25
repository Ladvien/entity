import json
import http.server
import socketserver
import threading
import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def local_duckdb_path(tmp_path: Path) -> Path:
    path = tmp_path / "db.duckdb"
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture()
def local_storage_dir(tmp_path: Path) -> Path:
    path = tmp_path / "storage"
    path.mkdir()
    yield path
    shutil.rmtree(path, ignore_errors=True)


class _OllamaHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # pragma: no cover - simple mock
        if self.path == "/api/tags":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # pragma: no cover - simple mock
        if self.path == "/api/generate":
            length = int(self.headers.get("content-length", 0))
            data = json.loads(self.rfile.read(length)) if length else {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps({"response": data.get("prompt", "")})
            self.wfile.write(resp.encode())
        else:
            self.send_error(404)

    def log_message(self, *args) -> None:  # pragma: no cover - silence log
        return


@pytest.fixture()
def mock_ollama_server() -> str:
    with socketserver.TCPServer(("localhost", 0), _OllamaHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://localhost:{server.server_address[1]}"
        try:
            yield url
        finally:
            server.shutdown()
            thread.join()
