import asyncio
import json

import pytest
import websockets

from entity.core.resources.container import ResourceContainer
from entity.resources.logging import LoggingResource


async def _connect(uri: str, attempts: int = 10, delay: float = 0.05):
    for _ in range(attempts):
        try:
            return await websockets.connect(uri)
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(delay)
    raise RuntimeError("WebSocket server not ready")


@pytest.mark.asyncio
async def test_websocket_broadcast(tmp_path, monkeypatch):
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
    stream = logger._stream_outputs[0]
    uri = f"ws://{stream.host}:{stream.port}"
    ws1 = await _connect(uri)
    ws2 = await _connect(uri)
    await logger.log("info", "message", component="test")
    msg1 = await asyncio.wait_for(ws1.recv(), timeout=2)
    msg2 = await asyncio.wait_for(ws2.recv(), timeout=2)
    for ws in (ws1, ws2):
        try:
            await ws.close()
        except websockets.exceptions.ConnectionClosedOK:
            pass
    await container.shutdown_all()
    assert json.loads(msg1)["message"] == "message"
    assert msg1 == msg2


@pytest.mark.asyncio
async def test_file_rotation(tmp_path, monkeypatch):
    log_file = tmp_path / "rot.log"
    container = ResourceContainer()
    monkeypatch.setattr(LoggingResource, "dependencies", [])
    container.register(
        "logging",
        LoggingResource,
        {
            "outputs": [
                {
                    "type": "structured_file",
                    "path": str(log_file),
                    "max_size": "1KB",
                    "backup_count": 1,
                }
            ]
        },
        layer=3,
    )
    await container.build_all()
    logger: LoggingResource = container.get("logging")  # type: ignore[assignment]
    for i in range(100):
        await logger.log("info", f"msg {i}", component="test")
    await container.shutdown_all()
    rotated = log_file.with_suffix(".1")
    assert rotated.exists()
