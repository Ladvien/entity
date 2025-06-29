from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from .manager import PipelineManager


class Message(BaseModel):
    message: str


class HTTPAdapter:
    """Simple FastAPI adapter for pipeline execution."""

    def __init__(self, manager: PipelineManager) -> None:
        self.manager = manager
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.post("/")
        async def handle(msg: Message) -> Dict[str, Any]:
            return await self.manager.run_pipeline(msg.message)
