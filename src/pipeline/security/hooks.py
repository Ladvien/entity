from __future__ import annotations

"""Validation hooks executed before each plugin stage."""

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List

from pipeline.stages import PipelineStage

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from pipeline.context import PluginContext

Validator = Callable[["PluginContext"], Awaitable[Any] | Any]


class StageInputValidator:
    """Manage per-stage input validation callbacks."""

    def __init__(self) -> None:
        self._hooks: Dict[PipelineStage, List[Validator]] = defaultdict(list)

    def register(self, stage: PipelineStage | str, validator: Validator) -> None:
        """Register a ``validator`` for ``stage``."""
        self._hooks[PipelineStage.ensure(stage)].append(validator)

    async def validate(self, stage: PipelineStage, context: PluginContext) -> None:
        """Run all validators registered for ``stage``."""
        for hook in self._hooks.get(stage, []):
            if asyncio.iscoroutinefunction(hook):
                await hook(context)
            else:
                hook(context)
