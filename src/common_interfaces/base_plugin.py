from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from pipeline.stages import PipelineStage


class BasePlugin(ABC):
    """Minimal interface implemented by all pipeline plugins."""

    stages: List["PipelineStage"]
    priority: int = 50
    dependencies: List[str] = []

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Execute plugin logic."""
        pass
