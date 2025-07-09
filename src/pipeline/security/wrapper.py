from __future__ import annotations

"""Security wrapper for tool plugins."""

from typing import Any, Dict

from pipeline.base_plugins import ToolPlugin

from .validation import InputValidator


class SecureToolWrapper(ToolPlugin):
    """Wrap another :class:`ToolPlugin` to enforce input validation."""

    def __init__(self, plugin: ToolPlugin, validator: InputValidator) -> None:
        super().__init__(plugin.config)
        self._plugin = plugin
        self._validator = validator
        self.stages = getattr(plugin, "stages", [])

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        validated = self._validator(params)
        sanitized = validated.model_dump()
        return await self._plugin.execute_function_with_retry(sanitized)
