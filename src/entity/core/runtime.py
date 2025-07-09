from __future__ import annotations

"""Minimal runtime executor."""

from dataclasses import dataclass, field
from typing import Any, Dict

from .registries import SystemRegistries


@dataclass
class AgentRuntime:
    registries: SystemRegistries
    manager: Any = field(init=False)

    def __post_init__(self) -> None:
        self.manager = None

    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        return {"message": message}

    async def handle(self, message: str) -> Dict[str, Any]:
        return await self.run_pipeline(message)
