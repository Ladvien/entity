from __future__ import annotations

"""Demonstration tool plugin, not production ready."""

from typing import Any, Dict, Protocol

from pipeline.base_plugins import ToolPlugin


class ToolBehavior(Protocol):
    async def run(self, params: Dict[str, Any]) -> Any: ...


class EchoBehavior:
    async def run(self, params: Dict[str, Any]) -> str:
        return str(params.get("text", ""))


class ComposedTool(ToolPlugin):
    """Tool plugin that delegates execution to a behavior object."""

    name = "composed_echo"

    def __init__(
        self, behavior: ToolBehavior | None = None, config: Dict | None = None
    ) -> None:
        super().__init__(config)
        self._behavior: ToolBehavior = behavior or EchoBehavior()

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        return await self._behavior.run(params)
