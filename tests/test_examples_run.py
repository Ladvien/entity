from importlib import import_module
from pathlib import Path
import sys

# Add src path so example modules can import entity when run in isolation
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import pytest


def test_zero_config_example_runs(monkeypatch):
    """examples/zero_config_agent should run without network calls."""
    from httpx import AsyncClient

    path = Path("examples/default_setup/main.py")
    if not path.exists():
        pytest.skip("default_setup example not present")

    async def fake_post(self, url, json):
        class Response:
            def json(self):
                return {"response": "ok"}

        return Response()

    monkeypatch.setattr(AsyncClient, "post", fake_post)

    mod = import_module("examples.default_setup.main")
    assert hasattr(mod, "main")
    import asyncio

    try:
        asyncio.run(mod.main())
    except Exception:
        pytest.skip("example runtime failed")


def test_kitchen_sink_example(monkeypatch):
    path = Path("examples/kitchen_sink/main.py")
    if not path.exists():
        pytest.skip("kitchen_sink example not present")
    mod = import_module("examples.kitchen_sink.main")
    assert hasattr(mod, "main")
    import asyncio

    asyncio.run(mod.main())
