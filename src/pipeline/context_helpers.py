from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

if TYPE_CHECKING:  # pragma: no cover - type check only
    from .context import PluginContext

from .errors import ToolExecutionError
from .state import ConversationEntry, FailureInfo
from .tools.base import RetryOptions
from .tools.execution import queue_tool_use


class AdvancedContext:
    """Advanced interface for ``PluginContext``."""

    def __init__(self, ctx: "PluginContext") -> None:
        self._ctx = ctx

    # ------------------------------------------------------------------
    def replace_conversation_history(
        self, new_history: List[ConversationEntry]
    ) -> None:
        """Replace entire conversation history with ``new_history``."""
        self._ctx._PluginContext__state.conversation = new_history  # type: ignore[attr-defined]

    async def wait_for_tool_result(self, result_key: str) -> Any:
        """Wait for a queued tool call to finish and return its result."""
        state = self._ctx._PluginContext__state  # type: ignore[attr-defined]
        if result_key not in state.stage_results:
            call = next(
                (c for c in state.pending_tool_calls if c.result_key == result_key),
                None,
            )
            if call is None:
                raise KeyError(result_key)
            tool = self._ctx._registries.tools.get(call.name)
            if not tool:
                result = f"Error: tool {call.name} not found"
                self._ctx.store(call.result_key, result)
                state.pending_tool_calls.remove(call)
                return result
            tool = cast(Any, tool)
            options = RetryOptions(
                max_retries=getattr(tool, "max_retries", 1),
                delay=getattr(tool, "retry_delay", 1.0),
            )
            try:
                result = await queue_tool_use(tool, call, state, options)
                self._ctx.store(call.result_key, result)
                self._ctx.record_tool_execution(call.name, call.result_key, call.source)
            except Exception as exc:  # noqa: BLE001
                result = f"Error: {exc}"
                self._ctx.store(call.result_key, result)
                self._ctx.record_tool_error(call.name, str(exc))
                state.failure_info = FailureInfo(
                    stage=str(state.current_stage),
                    plugin_name=call.name,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    original_exception=exc,
                )
                state.pending_tool_calls.remove(call)
                raise ToolExecutionError(call.name, exc, call.result_key)
            state.pending_tool_calls.remove(call)
        result = self._ctx.load(result_key)
        state.stage_results.pop(result_key, None)
        return result
