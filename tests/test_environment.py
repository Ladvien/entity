import os
import asyncio
import pytest
from entity.config.environment import load_env


def test_env_file_loading(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=env\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FOO", raising=False)

    load_env(env_file)

    assert os.environ["FOO"] == "env"


def test_env_does_not_override_existing(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BAR=env\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BAR", "os")

    load_env(env_file)

    assert os.environ["BAR"] == "os"


def test_secret_overrides_env_file(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BAZ=env\n")
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secret_file = secrets / "dev.env"
    secret_file.write_text("BAZ=secret\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BAZ", raising=False)

    load_env(env_file, env="dev")

    assert os.environ["BAZ"] == "secret"


def test_os_env_overrides_secret(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("QUX=env\n")
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secret_file = secrets / "prod.env"
    secret_file.write_text("QUX=secret\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QUX", "os")

    load_env(env_file, env="prod")

    assert os.environ["QUX"] == "os"


@pytest.mark.asyncio
async def test_ensure_ollama_pulls_when_missing(monkeypatch):
    from entity.utils.setup_manager import Layer0SetupManager
    from httpx import AsyncClient

    async def fake_get(self, url):
        class R:
            def json(self):
                return {"models": []}

        return R()

    async def fake_exec(*args, **kwargs):
        class P:
            returncode = 0

            async def communicate(self):
                return b"", b""

        return P()

    monkeypatch.setattr(AsyncClient, "get", fake_get)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    mgr = Layer0SetupManager()
    await mgr.ensure_ollama()


@pytest.mark.asyncio
async def test_ensure_ollama_download_failure(monkeypatch):
    from entity.utils.setup_manager import Layer0SetupManager
    from httpx import AsyncClient
    import pytest

    async def fake_get(self, url):
        class R:
            def json(self):
                return {"models": []}

        return R()

    async def fake_exec(*args, **kwargs):
        class P:
            returncode = 1

            async def communicate(self):
                return b"", b"boom"

        return P()

    monkeypatch.setattr(AsyncClient, "get", fake_get)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    mgr = Layer0SetupManager()
    with pytest.raises(RuntimeError):
        await mgr.ensure_ollama()
