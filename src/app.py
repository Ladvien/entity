from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from entity import Agent


class MessageRequest(BaseModel):
    message: str


def create_app(agent: Agent) -> FastAPI:
    """Build a FastAPI app that forwards requests to the agent."""

    app = FastAPI()

    # Disable HTTP proxy environment variables so httpx doesn't route
    # requests through the network when using ``AsyncClient(app=...)``
    for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        os.environ.pop(var, None)

    @app.post("/")
    async def handle(req: MessageRequest) -> Any:
        return await agent.handle(req.message)

    return app
