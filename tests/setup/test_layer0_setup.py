import asyncio
from pathlib import Path

import httpx
import pytest

from entity.utils.setup_manager import Layer0SetupManager


def test_setup_resources_created(tmp_path):
    db = tmp_path / "memory.duckdb"
    files = tmp_path / "files"
    mgr = Layer0SetupManager(db_path=str(db), files_dir=str(files))
    mgr.setup_resources()
    assert db.exists()
    assert files.exists()


@pytest.mark.asyncio
async def test_ensure_ollama_unavailable(monkeypatch):
    mgr = Layer0SetupManager()

    async def fake_get(self, url, timeout=2):
        raise httpx.RequestError("fail", request=None)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    result = await mgr.ensure_ollama()
    assert result is False


@pytest.mark.asyncio
async def test_ensure_ollama_missing_model(monkeypatch):
    mgr = Layer0SetupManager(model="foo")

    async def fake_get(self, url, timeout=2):
        class R:
            def json(self):
                return {"models": [{"name": "bar"}]}

        return R()

    async def fake_exec(*args, **kwargs):
        class P:
            returncode = 0

            async def communicate(self):
                return b"", b""

        return P()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    assert await mgr.ensure_ollama() is True


@pytest.mark.asyncio
async def test_setup_combined(monkeypatch, tmp_path):
    db = tmp_path / "db.duckdb"
    files = tmp_path / "files"
    mgr = Layer0SetupManager(db_path=str(db), files_dir=str(files))

    async def fake_get(self, url, timeout=2):
        class R:
            def json(self):
                return {"models": [{"name": mgr.model}]}

        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await mgr.setup()
    assert db.exists()
    assert files.exists()
