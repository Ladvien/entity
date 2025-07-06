"""Simple gRPC service exposing :class:`UnifiedLLMResource`."""

from __future__ import annotations

import asyncio
import os

import grpc

from entity_config.environment import load_env
from pipeline.resources.llm.unified import UnifiedLLMResource

from . import llm_pb2, llm_pb2_grpc


class LLMService(llm_pb2_grpc.LLMServiceServicer):
    """Text generation service using :class:`UnifiedLLMResource`."""

    def __init__(self, llm: UnifiedLLMResource | None = None) -> None:
        load_env()
        self._llm = llm or UnifiedLLMResource(
            {
                "provider": os.getenv("LLM_PROVIDER", "ollama"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "model": os.getenv("OLLAMA_MODEL", "tinyllama"),
            }
        )

    async def Generate(
        self, request: llm_pb2.GenerateRequest, context: grpc.aio.ServicerContext
    ) -> llm_pb2.GenerateResponse:
        """Stream generated tokens for ``request.prompt``."""

        try:
            async for token in self._llm.stream(request.prompt):
                yield llm_pb2.GenerateResponse(token=str(token))
        except Exception as exc:  # noqa: BLE001
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))


async def serve(port: int = 50051) -> None:
    """Run the example service."""
    server = grpc.aio.server()
    llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(serve())
