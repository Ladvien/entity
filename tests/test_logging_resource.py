import asyncio
import json

import pytest
import websockets

from entity.core.resources.container import ResourceContainer
from entity.resources.logging import LoggingResource
import os
import socket


async def _connect(uri: str, attempts: int = 10, delay: float = 0.05):
    for _ in range(attempts):
        try:
            return await websockets.connect(uri)
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(delay)
    raise RuntimeError("WebSocket server not ready")


@pytest.mark.asyncio
async def test_logging_file_and_console(tmp_path, capsys, monkeypatch):
    log_file = tmp_path / "log.jsonl"
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    container.register(
        "logging",
        LoggingResource,
        {
            "outputs": [
                {"type": "structured_file", "path": str(log_file)},
                {"type": "console"},
            ]
        },
        layer=3,
    )
    await container.build_all()
    logger: LoggingResource = container.get("logging")  # type: ignore[assignment]
    await logger.log("info", "hello", component="plugin", pipeline_id="1")
    await container.shutdown_all()

    captured = capsys.readouterr().out
    with open(log_file, "r", encoding="utf-8") as handle:
        data = json.loads(handle.readline())
    assert data["message"] == "hello"
    assert "hello" in captured


@pytest.mark.asyncio
async def test_logging_stream_output(tmp_path, monkeypatch):
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    container.register(
        "logging",
        LoggingResource,
        {"outputs": [{"type": "real_time_stream", "port": 0}]},
        layer=3,
    )
    await container.build_all()
    logger: LoggingResource = container.get("logging")  # type: ignore[assignment]
    stream = next(o for o in logger._stream_outputs)
    uri = f"ws://{stream.host}:{stream.port}"
    ws = await _connect(uri)
    await logger.log("info", "hi", component="resource")
    msg = await asyncio.wait_for(ws.recv(), timeout=2)
    try:
        await ws.close()
    except websockets.exceptions.ConnectionClosedOK:
        pass
    await container.shutdown_all()
    data = json.loads(msg)
    assert data["message"] == "hi"


@pytest.mark.asyncio
async def test_logging_auto_registration(monkeypatch):
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    await container.build_all()
    logger = container.get("logging")
    assert isinstance(logger, LoggingResource)
    await container.shutdown_all()


@pytest.mark.asyncio
async def test_log_rotation(tmp_path, monkeypatch):
    log_file = tmp_path / "log.jsonl"
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    container.register(
        "logging",
        LoggingResource,
        {
            "host_name": socket.gethostname(),
            "process_id": os.getpid(),
            "outputs": [
                {
                    "type": "structured_file",
                    "path": str(log_file),
                    "max_size": 10,
                    "backup_count": 1,
                }
            ],
        },
        layer=3,
    )
    await container.build_all()
    logger: LoggingResource = container.get("logging")  # type: ignore[assignment]
    await logger.log("info", "first", component="test")
    await logger.log("info", "second", component="test")
    await container.shutdown_all()

    rotated = log_file.with_name(log_file.name + ".1")
    assert rotated.exists()
    with rotated.open("r", encoding="utf-8") as handle:
        first_entry = json.loads(handle.readline())
    assert first_entry["message"] == "first"


@pytest.mark.asyncio
async def test_host_pid_included(tmp_path, monkeypatch):
    log_file = tmp_path / "log.jsonl"
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    container.register(
        "logging",
        LoggingResource,
        {"outputs": [{"type": "structured_file", "path": str(log_file)}]},
        layer=3,
    )
    await container.build_all()
    logger: LoggingResource = container.get("logging")  # type: ignore[assignment]
    await logger.log("info", "check", component="test")
    await container.shutdown_all()

    with log_file.open("r", encoding="utf-8") as handle:
        entry = json.loads(handle.readline())
    assert entry["host"] == socket.gethostname()
    assert entry["pid"] == os.getpid()
