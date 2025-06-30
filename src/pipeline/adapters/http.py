from __future__ import annotations

"""HTTP adapter exposing the pipeline through a FastAPI endpoint.

The :class:`HTTPAdapter` defined here spins up a small FastAPI
application with a single POST route. Incoming messages are forwarded
to the pipeline and the JSON response is returned to the caller.
"""

from typing import Any, cast

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from ..manager import PipelineManager
from ..pipeline import execute_pipeline
from ..plugins import AdapterPlugin
from ..registries import SystemRegistries
from ..stages import PipelineStage


class MessageRequest(BaseModel):
    message: str


class HTTPAdapter(AdapterPlugin):
    """HTTP adapter using FastAPI."""

    stages = [PipelineStage.DELIVER]

    def __init__(
        self, manager: PipelineManager | None = None, config: dict | None = None
    ) -> None:
        super().__init__(config)
        self.manager = manager
        self.app = FastAPI()
        self._registries: SystemRegistries | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.post("/")
        async def handle(req: MessageRequest) -> dict[str, Any]:
            if self.manager is not None:
                return await self.manager.run_pipeline(req.message)
            if self._registries is None:
                raise RuntimeError("Adapter not initialized")
            return cast(
                dict[str, Any], await execute_pipeline(req.message, self._registries)
            )

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
        server = uvicorn.Server(config)
        await server.serve()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
