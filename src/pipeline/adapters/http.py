from __future__ import annotations

"""HTTP adapter exposing the pipeline through a FastAPI endpoint.

The :class:`HTTPAdapter` defined here spins up a small FastAPI
application with a single POST route. Incoming messages are forwarded
to the pipeline and the JSON response is returned to the caller.
"""

import logging
import time
from collections import defaultdict, deque
from logging.handlers import RotatingFileHandler
from typing import Any, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter,
                               Summary)
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from registry import SystemRegistries

from ..manager import PipelineManager
from ..metrics import MetricsCollector
from ..observability.prometheus import PrometheusExporter
from ..pipeline import execute_pipeline
from ..plugins import AdapterPlugin
from ..stages import PipelineStage


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Validate bearer tokens on incoming requests."""

    def __init__(
        self, app: FastAPI, tokens: list[str], audit_logger: logging.Logger
    ) -> None:
        super().__init__(app)
        self.tokens = set(tokens)
        self.audit_logger = audit_logger

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if self.tokens:
            auth = request.headers.get("authorization")
            token = auth.split(" ")[-1] if auth and " " in auth else None
            if token not in self.tokens:
                client = request.client.host if request.client else "unknown"
                self.audit_logger.info("invalid token from %s", client)
                raise HTTPException(status_code=401, detail="Unauthorized")
        return await call_next(request)


class ThrottleMiddleware(BaseHTTPMiddleware):
    """Apply simple request rate limiting."""

    def __init__(
        self,
        app: FastAPI,
        requests: int,
        interval: float,
        audit_logger: logging.Logger,
    ) -> None:
        super().__init__(app)
        self.requests = requests
        self.interval = interval
        self.audit_logger = audit_logger
        self.access: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        key = request.headers.get("authorization")
        if key and " " in key:
            key = key.split(" ")[-1]
        else:
            key = request.client.host if request.client else "anonymous"

        record = self.access[key]
        now = time.monotonic()
        record.append(now)
        while record and now - record[0] > self.interval:
            record.popleft()
        if len(record) > self.requests:
            self.audit_logger.info("rate limit exceeded for %s", key)
            raise HTTPException(status_code=429, detail="Too Many Requests")
        return await call_next(request)


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
        self._setup_audit_logger()
        self._setup_middleware()
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

    def _setup_audit_logger(self) -> None:
        path = str(self.config.get("audit_log_path", "audit.log"))
        self.audit_logger = logging.getLogger("audit")
        if not self.audit_logger.handlers:
            handler = RotatingFileHandler(path, maxBytes=1_048_576, backupCount=5)
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)

    def _setup_middleware(self) -> None:
        tokens: list[str] = list(self.config.get("auth_tokens", []))
        if tokens:
            self.app.add_middleware(
                TokenAuthMiddleware, tokens=tokens, audit_logger=self.audit_logger
            )

        rl_cfg = self.config.get("rate_limit", {})
        requests = int(rl_cfg.get("requests", 0))
        interval = float(rl_cfg.get("interval", 60))
        if requests:
            self.app.add_middleware(
                ThrottleMiddleware,
                requests=requests,
                interval=interval,
                audit_logger=self.audit_logger,
            )

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
