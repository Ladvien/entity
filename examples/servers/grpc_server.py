"""Demo gRPC server using :class:`LLMGRPCAdapter`."""

from __future__ import annotations

import asyncio
import contextlib
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

import grpc
from plugins.builtin.adapters.grpc import LLMGRPCAdapter

from grpc_services import llm_pb2, llm_pb2_grpc
from pipeline.initializer import SystemInitializer


async def stream_prompt() -> None:
    """Connect to the server and print streamed tokens."""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = llm_pb2_grpc.LLMServiceStub(channel)
        request = llm_pb2.GenerateRequest(prompt="Hello world")
        async for resp in stub.Generate(request):
            print(resp.token, end="", flush=True)
    print()


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    adapter = LLMGRPCAdapter({"host": "[::]", "port": 50051})

    server_task = asyncio.create_task(adapter.serve(registries))
    await asyncio.sleep(0.5)
    await stream_prompt()
    await adapter.shutdown()
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task


if __name__ == "__main__":
    asyncio.run(main())
