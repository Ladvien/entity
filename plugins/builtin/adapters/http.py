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
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from pipeline.base_plugins import AdapterPlugin
from pipeline.exceptions import ResourceError
from pipeline.manager import PipelineManager
from pipeline.pipeline import execute_pipeline
from registry import SystemRegistries


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
        self.dashboard_enabled = bool(self.config.get("dashboard", False))
        self._server: uvicorn.Server | None = None
        self._registries: SystemRegistries | None = None
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
            return await self._handle_message(req.message)

        if self.dashboard_enabled:

            @self.app.get("/dashboard")
            async def dashboard() -> dict[str, Any]:
                count = 0
                if self.manager is not None:
                    count = self.manager.active_pipeline_count()
                return {"active_pipelines": count}

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
            return result
        except Exception as exc:  # pragma: no cover - adapter error path
            self.audit_logger.error(
                "pipeline error", extra={"error": str(exc)}, exc_info=True
            )
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

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
