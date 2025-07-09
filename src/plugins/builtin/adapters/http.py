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
from typing import Any, Awaitable, Callable, cast

from pipeline.context import PluginContext

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import Response
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from pipeline.base_plugins import AdapterPlugin
from pipeline.exceptions import ResourceError
from pipeline.manager import PipelineManager
from pipeline.metrics import MetricsCollector
from pipeline.observability import MetricsServerManager
from pipeline.pipeline import execute_pipeline
from pipeline.security import AdapterAuthenticator
from registry import SystemRegistries


class TokenAuthMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Validate bearer tokens on incoming requests."""

    def __init__(
        self,
        app: FastAPI,
        authenticator: AdapterAuthenticator,
        audit_logger: logging.Logger,
    ) -> None:
        super().__init__(app)
        self.auth = authenticator
        self.audit_logger = audit_logger

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if self.auth:
            auth = request.headers.get("authorization")
            token = auth.split(" ")[-1] if auth and " " in auth else None
            if not self.auth.authenticate(token) or not self.auth.authorize(
                token, "http"
            ):
                client = request.client.host if request.client else "unknown"
                self.audit_logger.info("invalid token from %s", client)
                for h in self.audit_logger.handlers:
                    h.flush()
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


class ThrottleMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
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

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
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
            if self.audit_logger.handlers:
                self.audit_logger.handlers[0].flush()
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        return await call_next(request)


class MessageRequest(BaseModel):  # type: ignore[misc]
    message: str


class HTTPAdapter(AdapterPlugin):
    """FastAPI based HTTP adapter for request/response handling."""

    def __init__(
        self,
        manager: PipelineManager[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(config)
        self.manager = manager
        tokens_cfg = self.config.get("auth_tokens", [])
        if isinstance(tokens_cfg, list):
            mapping = {t: ["http"] for t in tokens_cfg}
        else:
            mapping = {str(k): v for k, v in dict(tokens_cfg).items()}
        self.authenticator = AdapterAuthenticator(mapping) if mapping else None
        self.app = FastAPI()
        self._setup_audit_logger()
        self._setup_middleware()
        self.dashboard_enabled = bool(self.config.get("dashboard", False))
        if self.dashboard_enabled:
            MetricsServerManager.start()
        self._server: uvicorn.Server | None = None
        self._registries: SystemRegistries | None = None
        self._setup_routes()

    def _flush_audit_log(self) -> None:
        for handler in self.audit_logger.handlers:
            handler.flush()

    def _setup_audit_logger(self) -> None:
        path = str(self.config.get("audit_log_path", "audit.log"))
        self.audit_logger = logging.getLogger("audit")
        if self.audit_logger.handlers:
            for handler in list(self.audit_logger.handlers):
                self.audit_logger.removeHandler(handler)
                handler.close()
        handler = RotatingFileHandler(path, maxBytes=1_048_576, backupCount=5)
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)

    def _setup_middleware(self) -> None:
        if self.authenticator is not None:
            self.app.add_middleware(
                TokenAuthMiddleware,
                authenticator=self.authenticator,
                audit_logger=self.audit_logger,
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
        @self.app.post("/")  # type: ignore[misc]
        async def handle(req: MessageRequest) -> dict[str, Any]:
            return await self._handle_message(req.message)

        @self.app.get("/health")  # type: ignore[misc]
        async def health() -> dict[str, Any]:
            registries = self._registries
            if registries is None and self.manager is not None:
                registries = self.manager._registries
            if registries is None:
                return {"status": "starting"}
            report = await registries.resources.health_report()
            status = "ok" if all(report.values()) else "error"
            return {"status": status, "resources": report}

        if self.dashboard_enabled:

            @self.app.get("/dashboard")  # type: ignore[misc]
            async def dashboard() -> HTMLResponse:
                metrics = MetricsCollector()
                metrics.record_dashboard_request()
                server = MetricsServerManager.get()
                if server is not None:
                    server.update(metrics)
                count = 0
                if self.manager is not None:
                    count = self.manager.active_pipeline_count()
                html = (
                    "<!DOCTYPE html>"
                    "<html><head><title>Entity Dashboard</title>"
                    "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>"
                    "</head><body>"
                    f"<h1>Active pipelines: {count}</h1>"
                    "<canvas id='latency'></canvas>"
                    "<canvas id='failures'></canvas>"
                    "<script>async function load(){const res=await fetch('/metrics');"  # noqa: E501
                    "const text=await res.text();let lat=0;let fail=0;"  # noqa: E501
                    "for(const line of text.split('\\n')){if(line.startsWith('llm_latency_seconds_sum')){lat=parseFloat(line.split(' ')[1]);}if(line.startsWith('llm_failures_total')){fail=parseFloat(line.split(' ')[1]);}}"  # noqa: E501
                    "new Chart(document.getElementById('latency'),{type:'bar',data:{labels:['latency'],datasets:[{data:[lat]}]}});"  # noqa: E501
                    "new Chart(document.getElementById('failures'),{type:'bar',data:{labels:['failures'],datasets:[{data:[fail]}]}});}</script>"  # noqa: E501
                    "<script>load();</script></body></html>"
                )
                return HTMLResponse(html)

            @self.app.get("/metrics")  # type: ignore[misc]
            async def metrics() -> HTMLResponse:
                server = MetricsServerManager.get()
                if server is None:
                    return HTMLResponse(status_code=404)
                return HTMLResponse(server.render(), media_type="text/plain")

    async def _handle_message(self, message: str) -> dict[str, Any]:
        """Send a message through the pipeline and return the response."""
        try:
            if self.manager is not None:
                result = await self.manager.run_pipeline(message)
            else:
                if self._registries is None:
                    raise ResourceError("Adapter not initialized")
                result = cast(
                    dict[str, Any],
                    await execute_pipeline(message, self._registries),
                )
            self.audit_logger.info("request handled", extra={"status": "ok"})
            self._flush_audit_log()
            return result
        except Exception as exc:  # pragma: no cover - adapter error path
            self.audit_logger.error(
                "pipeline error", extra={"error": str(exc)}, exc_info=True
            )
            self._flush_audit_log()
            raise

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

    async def _execute_impl(
        self, context: PluginContext
    ) -> None:  # pragma: no cover - adapter
        pass
