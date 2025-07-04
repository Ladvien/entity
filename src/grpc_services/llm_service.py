"""Minimal gRPC service stub for model components."""

# mypy: ignore-errors

from __future__ import annotations

import asyncio

import grpc  # type: ignore

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
    """Example text generation service."""

    async def Generate(
        self, request: "llm_pb2.GenerateRequest", context: grpc.aio.ServicerContext
    ) -> "llm_pb2.GenerateResponse":  # type: ignore[name-defined]
        # TODO: integrate actual model inference
        for word in ["hello", "world"]:
            yield llm_pb2.GenerateResponse(token=word)


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
