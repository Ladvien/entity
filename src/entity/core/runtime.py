from __future__ import annotations

"""Minimal runtime executor."""

from dataclasses import dataclass, field
from typing import Any, Dict
import warnings

from .registries import SystemRegistries


@dataclass(init=False)
class _AgentRuntime:
    capabilities: SystemRegistries
    manager: Any = field(init=False)

    def __init__(
        self,
        capabilities: SystemRegistries | None = None,
        *,
        registries: SystemRegistries | None = None,
    ) -> None:
        if capabilities is None and registries is not None:
            warnings.warn(
                "'registries' is deprecated, use 'capabilities' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            capabilities = registries
        if capabilities is None:
            raise TypeError("capabilities is required")
        self.capabilities = capabilities
        self.__post_init__()

    def __post_init__(self) -> None:
        self.manager = None

    async def run_pipeline(self, message: str) -> Dict[str, Any]:
        return {"message": message}

    async def handle(self, message: str) -> Dict[str, Any]:
        return await self.run_pipeline(message)
