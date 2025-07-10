from __future__ import annotations

from typing import Any, Dict, Type

from pydantic import BaseModel

from entity.core.plugins import ToolPlugin
from entity.core.validation import PluginInputValidator


class InputValidator:
    """Validate tool input parameters using a Pydantic model."""

    def __init__(self, model: Type[BaseModel]) -> None:
        self._validator = PluginInputValidator(model)

    def validate(self, params: Dict[str, Any]) -> BaseModel:
        """Return sanitized ``params`` parsed into ``model``."""
        return self._validator.validate(params)

    def __call__(self, params: Dict[str, Any]) -> BaseModel:
        return self.validate(params)


class SecureToolWrapper:
    """Wrap a :class:`ToolPlugin` and validate parameters before execution."""

    def __init__(self, plugin: ToolPlugin, validator: InputValidator) -> None:
        self._plugin = plugin
        self._validator = validator

    async def execute(self, params: Dict[str, Any]) -> Any:
        validated = self._validator(params)
        if hasattr(validated, "model_dump"):
            clean = validated.model_dump()
        else:  # pragma: no cover - pydantic v1 fallback
            clean = validated.dict()
        return await self._plugin.execute_function(clean)


__all__ = ["InputValidator", "SecureToolWrapper"]
