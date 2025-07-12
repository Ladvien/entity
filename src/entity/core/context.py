from __future__ import annotations

"""Minimal plugin context objects.

This module exposes anthropomorphic helpers for plugins:

- ``think()`` / ``reflect()`` to share intermediate results between stages.
- ``say()`` to produce the final assistant response in OUTPUT stage.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from entity.core.state import ConversationEntry, PipelineState, ToolCall
import warnings
from pipeline.errors import PluginContextError
from pipeline.stages import PipelineStage


class AdvancedContext:
    """Low-level helpers for advanced plugin features."""

    def __init__(self, parent: "PluginContext") -> None:
        self._parent = parent

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    @property
    def parent(self) -> "PluginContext":
        return self._parent

    def replace_conversation_history(self, history: list[ConversationEntry]) -> None:
        self._parent._state.conversation = list(history)

    async def queue_tool_use(
        self,
        name: str,
        *,
        result_key: str | None = None,
        **params: Any,
    ) -> str:
        if self._parent._registries.tools.get(name) is None:
            raise ValueError(f"Tool '{name}' not found")
        if result_key is None:
            result_key = f"{name}_{len(self._parent._state.pending_tool_calls)}"
        self._parent._state.pending_tool_calls.append(
            ToolCall(name=name, params=params, result_key=result_key, source="queued")
        )
        return result_key

    def discover_tools(self, **filters: Any) -> list[tuple[str, Any]]:
        discover = getattr(self._parent._registries.tools, "discover", None)
        if callable(discover):
            return discover(**filters)
        return [
            (n, t)
            for n, t in getattr(self._parent._registries.tools, "_tools", {}).items()
        ]

    async def remember(self, key: str, value: Any) -> None:
        if self._parent._memory is not None:
            namespaced_key = f"{self._parent._user_id}:{key}"
            await self._parent._memory.set(namespaced_key, value)

    async def memory(self, key: str, default: Any | None = None) -> Any:
        if self._parent._memory is None:
            return default
        namespaced_key = f"{self._parent._user_id}:{key}"
        return await self._parent._memory.get(namespaced_key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._parent._state.metadata[key] = value

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        return self._parent._state.metadata.get(key, default)


class PluginContext:
    """Runtime context passed to plugins."""

    def __init__(
        self, state: PipelineState, registries: Any, user_id: str | None = None
    ) -> None:
        self._state = state
        self._registries = registries
        self._user_id = user_id or "default"
        # Use registry helper to fetch memory if registered
        self._memory = registries.resources.get("memory")
        self._plugin_name: str | None = None
        self._advanced = AdvancedContext(self)
        self._temporary_thoughts: dict[str, Any] = {}

    # ------------------------------------------------------------------
    @property
    def current_stage(self) -> Optional[PipelineStage]:
        return self._state.current_stage

    def set_current_stage(self, stage: PipelineStage) -> None:
        self._state.current_stage = stage

    def set_current_plugin(self, name: str) -> None:
        self._plugin_name = name

    @property
    def current_plugin(self) -> str | None:
        return self._plugin_name

    @property
    def pipeline_id(self) -> str:
        return self._state.pipeline_id

    @property
    def request_id(self) -> str:
        """Alias for ``pipeline_id`` for compatibility with logging."""
        return self.pipeline_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def response(self) -> Any:
        return self._state.response

    @property
    def advanced(self) -> AdvancedContext:
        """Return helpers for advanced plugins."""
        return self._advanced

    def has_response(self) -> bool:
        """Return ``True`` if a response has been set."""
        return self._state.response is not None

    def update_response(self, func: Callable[[Any], Any]) -> None:
        """Update ``response`` with ``func`` result."""
        self._state.response = func(self._state.response)

    def get_conversation_history(self) -> List[ConversationEntry]:
        return list(self._state.conversation)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def conversation(self) -> List[ConversationEntry]:
        """Return the current conversation history."""
        return self.get_conversation_history()

    def get_resource(self, name: str) -> Any | None:
        """Return the registered resource ``name`` or ``None`` when missing."""
        return self._registries.resources.get(name)

    def get_llm(self) -> Any | None:
        """Return the configured LLM resource."""
        return self._registries.resources.get("llm")

    def get_memory(self) -> Any | None:
        """Return the configured Memory resource."""
        return self.get_resource("memory")

    def get_storage(self) -> Any | None:
        """Return the configured Storage resource."""
        return self.get_resource("storage")

    def say(self, content: str, *, metadata: Dict[str, Any] | None = None) -> None:
        """Finalize the response in ``OUTPUT`` stage."""
        if self.current_stage is not PipelineStage.OUTPUT:
            raise PluginContextError(
                self.current_stage,
                self.current_plugin or "unknown",
                f"say may only be called in OUTPUT stage, not {self.current_stage}",
            )
        self._state.response = content
        self.add_conversation_entry(
            content=content,
            role="assistant",
            metadata=metadata,
        )

    async def call_llm(self, _context: Any, prompt: str, *, purpose: str = "") -> Any:
        llm = self._registries.resources.get("llm")
        if llm is None:

            class _Resp:
                content = ""

            return _Resp()
        if hasattr(llm, "generate"):
            return await llm.generate(prompt)
        func = getattr(llm, "__call__", None)
        if asyncio.iscoroutinefunction(func):
            return await func(prompt)
        if func:
            return func(prompt)

        class _Resp:
            content = ""

        return _Resp()

    async def ask_llm(self, prompt: str) -> str:
        result = await self.call_llm(self, prompt)
        return getattr(result, "content", str(result))

    def add_conversation_entry(
        self, *, content: str, role: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        self._state.conversation.append(
            ConversationEntry(
                content=content,
                role=role,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )
        )

    async def tool_use(self, name: str, **params: Any) -> Any:
        """Execute ``name`` immediately and return the result."""
        tool = self._registries.tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        result = await tool.execute_function(params)
        return result

    async def queue_tool_use(
        self, name: str, *, result_key: str | None = None, **params: Any
    ) -> str:
        warnings.warn(
            "PluginContext.queue_tool_use is deprecated; use context.advanced.queue_tool_use",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.advanced.queue_tool_use(name, result_key=result_key, **params)

    def discover_tools(self, **filters: Any) -> list[tuple[str, Any]]:
        warnings.warn(
            "PluginContext.discover_tools is deprecated; use context.advanced.discover_tools",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.advanced.discover_tools(**filters)

    # ------------------------------------------------------------------
    # Stage result helpers ("think"/"reflect")
    # ------------------------------------------------------------------

    def store(self, key: str, value: Any) -> None:
        """Persist ``value`` for later pipeline stages."""
        if (
            self._state.max_stage_results is not None
            and len(self._state.stage_results) >= self._state.max_stage_results
        ):
            oldest = next(iter(self._state.stage_results))
            del self._state.stage_results[oldest]
        self._state.stage_results[key] = value

    def think(self, key: str, value: Any) -> None:
        """Alias for :meth:`store` using anthropomorphic naming."""
        self.store(key, value)

    def load(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a stored value."""
        return self._state.stage_results.get(key, default)

    def reflect(self, key: str, default: Any | None = None) -> Any:
        """Alias for :meth:`load` using anthropomorphic naming."""
        return self.load(key, default)

    def has(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in stage results."""
        return key in self._state.stage_results

    # ------------------------------------------------------------------
    # Anthropomorphic temporary storage helpers
    # ------------------------------------------------------------------

    async def think(self, key: str, value: Any) -> None:
        """Store a temporary value for later reflection."""
        self._temporary_thoughts[key] = value

    async def reflect(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a previously stored thought."""
        return self._temporary_thoughts.get(key, default)

    async def clear_thoughts(self) -> None:
        """Remove all stored thoughts."""
        self._temporary_thoughts.clear()

    # ------------------------------------------------------------------
    # Persistent memory helpers
    # ------------------------------------------------------------------

    async def remember(self, key: str, value: Any) -> None:
        warnings.warn(
            "PluginContext.remember is deprecated; use context.advanced.remember",
            DeprecationWarning,
            stacklevel=2,
        )
        await self.advanced.remember(key, value)

    async def memory(self, key: str, default: Any | None = None) -> Any:
        warnings.warn(
            "PluginContext.memory is deprecated; use context.advanced.memory",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.advanced.memory(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        warnings.warn(
            "PluginContext.set_metadata is deprecated; use context.advanced.set_metadata",
            DeprecationWarning,
            stacklevel=2,
        )
        self.advanced.set_metadata(key, value)

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        warnings.warn(
            "PluginContext.get_metadata is deprecated; use context.advanced.get_metadata",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.advanced.get_metadata(key, default)

    @property
    def failure_info(self) -> Any:
        """Return information about the most recent failure."""
        return self._state.failure_info

    def set_response(self, value: Any) -> None:
        warnings.warn(
            "PluginContext.set_response is deprecated; use context.say",
            DeprecationWarning,
            stacklevel=2,
        )
        self.say(value)
