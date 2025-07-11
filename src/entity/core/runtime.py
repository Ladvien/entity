from __future__ import annotations

"""Minimal runtime executor."""

from dataclasses import dataclass, field
from typing import Any, Dict

from .registries import SystemRegistries


@dataclass(init=False)
class _AgentRuntime:
    capabilities: SystemRegistries
    manager: Any = field(init=False)

    def __init__(self, capabilities: SystemRegistries) -> None:
        self.capabilities = capabilities
        self.__post_init__()

    def __post_init__(self) -> None:
        self.manager = None

    async def run_pipeline(
        self, message: str, *, user_id: str | None = None
    ) -> Dict[str, Any]:
        return {"message": message, "user_id": user_id or "default"}

    async def handle(
        self, message: str, *, user_id: str | None = None
    ) -> Dict[str, Any]:
        return await self.run_pipeline(message, user_id=user_id)


# Public alias for backwards compatibility and clearer imports
AgentRuntime = _AgentRuntime

__all__ = ["AgentRuntime", "_AgentRuntime"]
