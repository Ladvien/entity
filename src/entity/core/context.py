from __future__ import annotations

"""Minimal plugin context objects."""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from entity.core.state import ConversationEntry, PipelineState
from pipeline.errors import PluginContextError
from pipeline.stages import PipelineStage


class PluginContext:
    """Runtime context passed to plugins."""

    def __init__(
        self, state: PipelineState, registries: Any, user_id: str | None = None
    ) -> None:
        self._state = state
        self._registries = registries
        self._user_id = user_id or "default"
        self._memory = getattr(registries.resources, "memory", None)
        self._plugin_name: str | None = None

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
    def user_id(self) -> str:
        return self._user_id

    @property
    def response(self) -> Any:
        return self._state.response

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

    def say(self, content: str, *, metadata: Dict[str, Any] | None = None) -> None:
        """Append an assistant message to the conversation."""
        self.add_conversation_entry(
            content=content, role="assistant", metadata=metadata
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
        get_cached = getattr(self._registries.tools, "get_cached_result", None)
        cache_result = getattr(self._registries.tools, "cache_result", None)
        cached = await get_cached(name, params) if get_cached else None
        if cached is not None:
            result = cached
            duration = 0.0
        else:
            start = time.perf_counter()
            result = await tool.execute_function(params)
            duration = time.perf_counter() - start
            if cache_result:
                await cache_result(name, params, result)
        # Tool duration metrics removed
        return result

    async def queue_tool_use(
        self, name: str, *, result_key: str | None = None, **params: Any
    ) -> str:
        """Queue ``name`` for later execution and return its result key."""
        if self._registries.tools.get(name) is None:
            raise ValueError(f"Tool '{name}' not found")
        if result_key is None:
            result_key = f"{name}_{len(self._state.pending_tool_calls)}"
        self._state.pending_tool_calls.append(
            ToolCall(name=name, params=params, result_key=result_key, source="queued")
        )
        return result_key

    def discover_tools(self, **filters: Any) -> list[tuple[str, Any]]:
        """Return registered tools matching ``filters``."""
        discover = getattr(self._registries.tools, "discover", None)
        if callable(discover):
            return discover(**filters)
        # Fallback: return all tools if registry lacks discovery helper
        return [
            (n, t) for n, t in getattr(self._registries.tools, "_tools", {}).items()
        ]

    # ------------------------------------------------------------------
    # Stage result helpers
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

    def load(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a stored value."""
        return self._state.stage_results.get(key, default)

    def has(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in stage results."""
        return key in self._state.stage_results

    # ------------------------------------------------------------------
    # Persistent memory helpers
    # ------------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Persist ``value`` in the configured memory resource."""
        if self._memory is not None:
            namespaced_key = f"{self._user_id}:{key}"
            self._memory.remember(namespaced_key, value)

    def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from persistent memory."""
        if self._memory is None:
            return default
        namespaced_key = f"{self._user_id}:{key}"
        return self._memory.get(namespaced_key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._state.metadata[key] = value

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        return self._state.metadata.get(key, default)

    @property
    def failure_info(self) -> Any:
        """Return information about the most recent failure."""
        return self._state.failure_info

    def set_response(self, value: Any) -> None:
        if self.current_stage is not PipelineStage.DELIVER:
            raise PluginContextError(
                self.current_stage,
                self.current_plugin or "unknown",
                f"set_response may only be called in DELIVER stage, not {self.current_stage}",
            )
        self._state.response = value
