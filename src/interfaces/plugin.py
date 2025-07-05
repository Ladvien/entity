from __future__ import annotations

from typing import Any, Awaitable, Dict, Protocol, TypeVar

ToolResultT = TypeVar("ToolResultT", covariant=True)


class ToolPluginProtocol(Protocol[ToolResultT]):
    """Interface for tool plugins."""

    max_retries: int
    retry_delay: float

    async def execute_function_with_retry(
        self, params: Dict[str, Any], max_retries: int, delay: float
    ) -> ToolResultT: ...

    async def execute_function(self, params: Dict[str, Any]) -> ToolResultT: ...

    def run(self, params: Dict[str, Any]) -> Awaitable[ToolResultT] | ToolResultT: ...


ResourceT = TypeVar("ResourceT", covariant=True)


class ResourcePluginProtocol(Protocol):
    """Interface for resource plugins."""

    async def initialize(self) -> None: ...

    async def health_check(self) -> bool: ...

    def get_metrics(self) -> Dict[str, Any]: ...
