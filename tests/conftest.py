import json
import os
import shutil
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import pytest

from entity_config.environment import load_env

SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture(autouse=True)
def _load_test_env():
    """Load environment variables for tests."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_env(env_path)
    yield


@pytest.fixture(scope="session")
def postgres_service(postgresql_proc):
    """Start a temporary PostgreSQL instance if available."""
    if shutil.which("pg_ctl") is None:
        pytest.skip("PostgreSQL server not installed")
    if os.geteuid() == 0:
        pytest.skip("PostgreSQL cannot run as root")
    return postgresql_proc


@pytest.fixture()
def pg_env(postgres_service, postgresql):
    """Provide environment variables for the temporary PostgreSQL server."""
    os.environ.update(
        {
            "DB_HOST": postgresql.info.host,
            "DB_NAME": postgresql.info.dbname,
            "DB_USERNAME": postgresql.info.user,
            "DB_PASSWORD": postgresql.info.password or "",
        }
    )
    yield postgresql


@pytest.fixture()
def mock_llm_server():
    """Start a simple HTTP server returning predefined JSON."""

    class Handler(BaseHTTPRequestHandler):
        response: dict = {}
        request_path: str = ""
        request_body: bytes = b""

        def do_POST(self):  # pragma: no cover - minimal server
            Handler.request_path = self.path
            Handler.request_body = self.rfile.read(
                int(self.headers.get("Content-Length", 0))
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(Handler.response).encode())

    server = HTTPServer(("localhost", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, Handler
    finally:
        server.shutdown()
        thread.join()
