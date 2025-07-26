import asyncio
import os
<<<<<<< HEAD
=======
import runpy
>>>>>>> pr-1943
import sys

import asyncio
import socketserver
import threading

from tests.fixtures.local_resources import _OllamaHandler
import pytest


@pytest.mark.examples
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_advanced_workflow(monkeypatch, capsys):
    monkeypatch.setattr(
        "entity.setup.ollama_installer.OllamaInstaller.ensure_ollama_available",
        lambda model=None: None,
    )
<<<<<<< HEAD
    print(f"STDOUT: {proc.stdout}")
    print(f"STDERR: {proc.stderr}")  # ← Add this to see errors
    print(f"Return code: {proc.returncode}")
    assert proc.stdout.strip() == "Result: 4"
=======
    monkeypatch.setattr(
        "entity.infrastructure.ollama_infra.OllamaInfrastructure.health_check",
        lambda self: False,
    )
    sys.path.insert(0, "src")
    sys.path.insert(0, ".")
    import importlib

    mod = importlib.import_module("examples.advanced_workflow")
    await mod.main()
    captured = capsys.readouterr()
    assert captured.out.strip().endswith("Result: 4")
>>>>>>> pr-1942
=======
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
>>>>>>> pr-1943
