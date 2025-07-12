import asyncio
import json

import pytest
import websockets

from entity.core.resources.container import ResourceContainer
from entity.resources.logging import LoggingResource


@pytest.mark.asyncio
async def test_logging_file_and_console(tmp_path, capsys):
    log_file = tmp_path / "log.jsonl"
    container = ResourceContainer()
    container.register(
        "logging",
        LoggingResource,
        {"outputs": [{"type": "structured_file", "path": str(log_file)}]},
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
async def test_logging_stream_output(tmp_path):
    container = ResourceContainer()
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
    async with websockets.connect(uri) as ws:
        await logger.log("info", "hi", component="resource")
        msg = await asyncio.wait_for(ws.recv(), timeout=2)
    await container.shutdown_all()
    data = json.loads(msg)
    assert data["message"] == "hi"


@pytest.mark.asyncio
async def test_logging_auto_registration():
    container = ResourceContainer()
    await container.build_all()
    logger = container.get("logging")
    assert isinstance(logger, LoggingResource)
    await container.shutdown_all()
