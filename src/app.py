from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from entity import Agent


class MessageRequest(BaseModel):
    message: str


def create_app(agent: Agent) -> FastAPI:
    """Build a FastAPI app that forwards requests to the agent."""

    app = FastAPI()

    @app.post("/")
    async def handle(req: MessageRequest) -> Any:
        return await agent.handle(req.message)

    return app
