from importlib import import_module
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_zero_config_example_runs(monkeypatch):
    """examples/zero_config_agent should run without network calls."""
    from httpx import AsyncClient

    async def fake_post(self, url, json):
        class R:
            def json(self):
                return {"response": "ok"}

        return R()

    monkeypatch.patch.object(AsyncClient, "post", fake_post)

    mod = import_module("examples.zero_config_agent.main")
    assert hasattr(mod, "main")
    await mod.main()


@pytest.mark.asyncio
async def test_kitchen_sink_example(monkeypatch):
    path = Path("examples/kitchen_sink/main.py")
    if not path.exists():
        pytest.skip("kitchen_sink example not present")
    mod = import_module("examples.kitchen_sink.main")
    assert hasattr(mod, "main")
    await mod.main()
