import os
import runpy
import sys

import asyncio
import socketserver
import threading

from tests.fixtures.local_resources import _OllamaHandler
import pytest


@pytest.mark.examples
def test_advanced_workflow(capsys):
    with socketserver.TCPServer(("localhost", 0), _OllamaHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        os.environ["ENTITY_OLLAMA_URL"] = f"http://localhost:{server.server_address[1]}"
        sys.path.insert(0, "src")
        import examples.advanced_workflow as aw

        asyncio.run(aw.main())
        captured = capsys.readouterr()
        server.shutdown()
        thread.join()

    assert captured.out.strip() == "Result: 4"
