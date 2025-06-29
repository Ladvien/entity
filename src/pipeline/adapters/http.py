from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from ..pipeline import SystemRegistries, execute_pipeline
from ..plugins import AdapterPlugin


class MessageRequest(BaseModel):
    message: str


class HttpAdapter(AdapterPlugin):
    """Simple HTTP adapter using FastAPI."""

    stages: list = []

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)
        self.app = FastAPI()
        self._registries: SystemRegistries | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.post("/")
        async def handle(req: MessageRequest):
            if self._registries is None:
                raise RuntimeError("Adapter not initialized")
            return await execute_pipeline(req.message, self._registries)

    async def serve(self, registries: SystemRegistries) -> None:
        self._registries = registries
        host = self.config.get("host", "127.0.0.1")
        port = int(self.config.get("port", 8000))
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def _execute_impl(self, context):
        pass
