from __future__ import annotations

"""HTTP adapter exposing the pipeline through a FastAPI endpoint.

The :class:`HTTPAdapter` defined here spins up a small FastAPI
application with a single POST route. Incoming messages are forwarded
to the pipeline and the JSON response is returned to the caller.
"""

from typing import Any, cast

import uvicorn
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Summary
from pydantic import BaseModel

from registry import SystemRegistries

from ..manager import PipelineManager
from ..metrics import MetricsCollector
from ..observability.prometheus import PrometheusExporter
from ..pipeline import execute_pipeline
from ..plugins import AdapterPlugin
from ..stages import PipelineStage


class MessageRequest(BaseModel):
    message: str


class HTTPAdapter(AdapterPlugin):
    """FastAPI based HTTP adapter for request/response handling."""

    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

    def __init__(
        self,
        manager: PipelineManager | None = None,
        config: dict | None = None,
    ) -> None:
        super().__init__(config)
        self.manager = manager
        self.app = FastAPI()
        self._server: uvicorn.Server | None = None
        self._registries: SystemRegistries | None = None
        self.registry = CollectorRegistry()
        self.exporter = PrometheusExporter(self.registry)
        self.request_counter = Counter(
            "requests_total",
            "Total HTTP requests",
            registry=self.registry,
        )
        self.request_latency = Summary(
            "request_latency_seconds",
            "Latency of HTTP requests",
            registry=self.registry,
        )
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.post("/")
        async def handle(req: MessageRequest) -> dict[str, Any]:
            self.request_counter.inc()
            with self.request_latency.time():
                result, metrics = await self._handle_message_with_metrics(req.message)
                self.exporter.record(metrics)
                return result

        @self.app.get("/health")
        async def health() -> dict[str, Any]:
            if self._registries is None:
                raise RuntimeError("Adapter not initialized")
            status: dict[str, bool] = {}
            healthy = True
            for name in self._registries.resources.names():
                resource = self._registries.resources.get(name)
                ok = False
                try:
                    ok = await resource.health_check()
                except Exception:
                    ok = False
                status[name] = ok
                if not ok:
                    healthy = False
            return {
                "status": "healthy" if healthy else "unhealthy",
                "resources": status,
            }

        @self.app.get("/metrics")
        async def metrics() -> Response:
            data = self.exporter.generate_latest()
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    async def _handle_message_with_metrics(
        self, message: str
    ) -> tuple[dict[str, Any], MetricsCollector]:
        if self.manager is not None:
            if self.manager._registries is None:
                raise RuntimeError("Adapter not initialized")
            return cast(
                tuple[dict[str, Any], MetricsCollector],
                await execute_pipeline(
                    message,
                    self.manager._registries,
                    pipeline_manager=self.manager,
                    return_metrics=True,
                ),
            )
        if self._registries is None:
            raise RuntimeError("Adapter not initialized")
        return cast(
            tuple[dict[str, Any], MetricsCollector],
            await execute_pipeline(message, self._registries, return_metrics=True),
        )

    async def _handle_message(self, message: str) -> dict[str, Any]:
        """Send a message through the pipeline and return the response."""
        result, _ = await self._handle_message_with_metrics(message)
        return result

    async def serve(self, registries: SystemRegistries) -> None:
        """Start the FastAPI HTTP server.

        Parameters
        ----------
        registries:
            System registries containing all initialized plugins and resources.
        """
        self._registries = registries
        host = self.config.get("host", "127.0.0.1")
        port = int(self.config.get("port", 8000))
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        self._server = uvicorn.Server(config)
        await self._server.serve()

    async def shutdown(self) -> None:
        """Gracefully stop the running server, if any."""
        if self._server is not None:
            await self._server.shutdown()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
