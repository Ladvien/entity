import asyncio
from types import SimpleNamespace

import httpx
import pytest

from entity.infrastructure.llamacpp import LlamaCppInfrastructure


@pytest.mark.asyncio
async def test_validate_runtime_success(monkeypatch):
    infra = LlamaCppInfrastructure({"host": "localhost", "port": 9999})

    async def fake_get(self, url, timeout=5.0):
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    result = await infra.validate_runtime()
    assert result.success


@pytest.mark.asyncio
async def test_initialize_and_shutdown(monkeypatch):
    calls = {}

    class DummyProc:
        def terminate(self):
            calls["terminated"] = True

        async def wait(self):
            calls["waited"] = True

    async def fake_exec(*_args, **_kwargs):
        calls["started"] = True
        return DummyProc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    infra = LlamaCppInfrastructure({"binary": "dummy", "model": "foo"})
    await infra.initialize()
    assert calls.get("started")
    assert infra._process is not None

    await infra.shutdown()
    assert calls.get("terminated")
    assert calls.get("waited")
    assert infra._process is None
