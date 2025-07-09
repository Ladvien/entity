from __future__ import annotations

"""Plugin context utilities for Entity plugins."""

from typing import Any

from pipeline.context import AdvancedContext as BaseAdvancedContext
from pipeline.context import PluginContext as BasePluginContext
from pipeline.state import ConversationEntry

__all__ = ["PluginContext", "ConversationEntry", "AdvancedContext"]


class PluginContext(BasePluginContext):
    """Entity wrapper around :class:`pipeline.context.PluginContext`."""

    def store(self, key: str, value: Any) -> None:
        """Store intermediate ``value`` for the current stage under ``key``."""
        state = self._PluginContext__state
        if key in state.stage_results:
            raise ValueError(f"Stage result '{key}' already set")
        state.stage_results[key] = value
        max_results = state.max_stage_results
        if max_results is not None and len(state.stage_results) > max_results:
            oldest = next(iter(state.stage_results))
            if oldest != key:
                state.stage_results.pop(oldest, None)

    def load(self, key: str) -> Any:
        """Retrieve a stage result previously stored via :meth:`store`."""
        if key not in self._PluginContext__state.stage_results:
            raise KeyError(key)
        return self._PluginContext__state.stage_results[key]

    def has(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in stage results."""
        return key in self._PluginContext__state.stage_results


AdvancedContext = BaseAdvancedContext
