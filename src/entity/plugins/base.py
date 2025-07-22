from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """Base class for all plugins."""

    stage: str | None = None
    dependencies: list[str] = []

    def __init__(self, resources: dict[str, Any]):
        self.resources = resources

    async def execute(self, context: Any) -> Any:
        """Validate and run the plugin implementation."""
        self._enforce_stage(context)
        self._validate_dependencies()
        try:
            return await self._execute_impl(context)
        except Exception:  # pragma: no cover - simple example
            # In real system we'd log the error and propagate.
            raise

    def _enforce_stage(self, context: Any) -> None:
        expected = self.stage
        current = getattr(context, "current_stage", None)
        if expected and current != expected:
            raise RuntimeError(
                f"{self.__class__.__name__} cannot run in stage '{current}'"
            )

    def _validate_dependencies(self) -> None:
        missing = [dep for dep in self.dependencies if dep not in self.resources]
        if missing:
            raise RuntimeError(
                f"Missing dependencies for {self.__class__.__name__}: {', '.join(missing)}"
            )

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Plugin-specific execution logic."""
        raise NotImplementedError
