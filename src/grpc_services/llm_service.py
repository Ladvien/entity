"""Minimal gRPC service stub for model components."""

# mypy: ignore-errors

from __future__ import annotations

import asyncio
import os
from typing import Any

import grpc  # type: ignore

from config.environment import load_env
from pipeline.resources.llm.unified import UnifiedLLMResource

# These modules are generated from ``llm.proto`` using ``grpcio-tools``.
# They are intentionally excluded from version control and should be
# regenerated when the protocol changes.
try:  # pragma: no cover - stubs for illustration
    from . import llm_pb2, llm_pb2_grpc  # type: ignore
except Exception:  # pragma: no cover - stub fallback
    llm_pb2 = None
    llm_pb2_grpc = None


class LLMService(
    llm_pb2_grpc.LLMServiceServicer if llm_pb2_grpc else object
):  # type: ignore[misc]
    """Text generation service using :class:`UnifiedLLMResource`."""

    def __init__(self, llm: Any | None = None) -> None:
        load_env()
        self.llm = llm or UnifiedLLMResource(
            {
                "provider": os.getenv("LLM_PROVIDER", "ollama"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "tinyllama"),
            }
        )

    async def Generate(
        self, request: "llm_pb2.GenerateRequest", context: grpc.aio.ServicerContext
    ) -> "llm_pb2.GenerateResponse":  # type: ignore[name-defined]
        """Stream generated tokens for ``request.prompt``."""

        try:
            async for token in self.llm.stream(request.prompt):
                yield llm_pb2.GenerateResponse(token=str(token))
        except Exception as exc:  # noqa: BLE001
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))


async def serve(port: int = 50051) -> None:
    """Run the example service."""
    server = grpc.aio.server()
    if llm_pb2_grpc:
        llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(serve())
