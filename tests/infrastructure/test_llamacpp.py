import asyncio
<<<<<<< HEAD

=======
from types import SimpleNamespace

import httpx
>>>>>>> pr-1480
import pytest

from entity.infrastructure.llamacpp import LlamaCppInfrastructure


<<<<<<< HEAD
class FakeProcess:
    def __init__(self):
        self.terminated = False
        self.waited = False
        self.killed = False

    def terminate(self):
        self.terminated = True

    async def wait(self):
        self.waited = True
        return 0

    def kill(self):
        self.killed = True
=======
@pytest.mark.asyncio
async def test_validate_runtime_success(monkeypatch):
    infra = LlamaCppInfrastructure({"host": "localhost", "port": 9999})

    async def fake_get(self, url, timeout=5.0):
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    result = await infra.validate_runtime()
    assert result.success
>>>>>>> pr-1480


@pytest.mark.asyncio
async def test_initialize_and_shutdown(monkeypatch):
    calls = {}

<<<<<<< HEAD
    async def fake_exec(*args, **kwargs):
        calls["args"] = list(args)
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    infra = LlamaCppInfrastructure(
        {
            "binary": "foo",
            "model": "bar.bin",
            "host": "0.0.0.0",
            "port": 1234,
            "args": ["--threads", "1"],
        }
    )
    await infra.initialize()
    proc = infra._proc
    assert calls["args"][0] == "foo"
    assert "--model" in calls["args"]
    assert proc is not None

    await infra.shutdown()
    assert proc.terminated
    assert proc.waited
    assert infra._proc is None


@pytest.mark.asyncio
async def test_validate_runtime(monkeypatch):
    class R:
        def __init__(self, code):
            self.status_code = code

    async def fake_get(self, url):
        return R(200)

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get, raising=False)
    infra = LlamaCppInfrastructure({"model": "m"})
    assert await infra.validate_runtime() is True

    async def fake_get_bad(self, url):
        raise RuntimeError

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get_bad, raising=False)
    assert await infra.validate_runtime() is False
=======
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
>>>>>>> pr-1480
