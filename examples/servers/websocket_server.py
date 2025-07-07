"""Run a simple WebSocket server using the Entity framework."""

from __future__ import annotations

import asyncio
import contextlib
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.adapters.websocket import WebSocketAdapter

from pipeline import PipelineManager
from pipeline.initializer import SystemInitializer


async def send_test_message() -> None:
    import websockets

    uri = "ws://127.0.0.1:8001/"
    async with websockets.connect(uri) as websocket:
        await websocket.send("hello")
        response = await websocket.recv()
        print("Received:", response)


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    manager = PipelineManager(registries)
    adapter = WebSocketAdapter(manager, {"host": "127.0.0.1", "port": 8001})

    server_task = asyncio.create_task(adapter.serve(registries))
    await asyncio.sleep(1)
    await send_test_message()
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task


if __name__ == "__main__":
    asyncio.run(main())
