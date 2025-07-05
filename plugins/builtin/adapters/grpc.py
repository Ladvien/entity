from __future__ import annotations

"""gRPC adapter exposing :class:`LLMService`."""

import grpc

from grpc_services import llm_pb2_grpc
from grpc_services.llm_service import LLMService
from pipeline.base_plugins import AdapterPlugin
from pipeline.stages import PipelineStage
from registry import SystemRegistries


class LLMGRPCAdapter(AdapterPlugin):
    """Serve :class:`LLMService` over gRPC."""

    stages = [PipelineStage.DELIVER]

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)
        self._server: grpc.aio.Server | None = None

    async def serve(self, registries: SystemRegistries) -> None:  # noqa: ARG002
        """Start the gRPC server."""
        self._server = grpc.aio.server()
        llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), self._server)
        host = self.config.get("host", "[::]")
        port = int(self.config.get("port", 50051))
        self._server.add_insecure_port(f"{host}:{port}")
        await self._server.start()
        await self._server.wait_for_termination()

    async def shutdown(self) -> None:
        """Stop the server if running."""
        if self._server is not None:
            await self._server.stop(0)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
