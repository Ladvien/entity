from __future__ import annotations

"""Minimal plugin context objects."""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pipeline.stages import PipelineStage
from entity.core.state import ConversationEntry, PipelineState


class PluginContext:
    """Runtime context passed to plugins."""

    def __init__(self, state: PipelineState, registries: Any) -> None:
        self._state = state
        self._registries = registries
        self._cache: Dict[str, Any] = {}
        self._memory = getattr(registries.resources, "memory", None)

    # ------------------------------------------------------------------
    @property
    def current_stage(self) -> Optional[PipelineStage]:
        return self._state.current_stage

    def set_current_stage(self, stage: PipelineStage) -> None:
        self._state.current_stage = stage

    @property
    def pipeline_id(self) -> str:
        return self._state.pipeline_id

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
        cached = await self._registries.tools.get_cached_result(name, params)
        if cached is not None:
            result = cached
            duration = 0.0
        else:
            start = time.perf_counter()
            result = await tool.execute_function(params)
            duration = time.perf_counter() - start
            await self._registries.tools.cache_result(name, params, result)
        if self._state.metrics:
            key = f"{self.current_stage}:{name}"
            self._state.metrics.record_tool_duration(key, duration)
        return result

    async def queue_tool_use(
        self, name: str, *, result_key: str | None = None, **params: Any
    ) -> str:
        """Queue ``name`` for later execution and return its result key."""
        if result_key is None:
            result_key = f"{name}_{len(self._state.pending_tool_calls)}"
        self._state.pending_tool_calls.append(
            ToolCall(name=name, params=params, result_key=result_key, source="queued")
        )
        return result_key

    # ------------------------------------------------------------------
    # Temporary cache helpers
    # ------------------------------------------------------------------

    def cache(self, key: str, value: Any) -> None:
        """Store a temporary value for this pipeline run."""
        self._cache[key] = value

    def recall(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a cached value."""
        return self._cache.get(key, default)

    def has(self, key: str) -> bool:
        """Return True if ``key`` exists in the cache."""
        return key in self._cache

    # ------------------------------------------------------------------
    # Persistent memory helpers
    # ------------------------------------------------------------------

    def remember(self, key: str, value: Any) -> None:
        """Persist ``value`` in the configured memory resource."""
        if self._memory is not None:
            self._memory.remember(key, value)

    def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from persistent memory."""
        if self._memory is None:
            return default
        return self._memory.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._state.metadata[key] = value

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        return self._state.metadata.get(key, default)

    @property
    def failure_info(self) -> Any:
        """Return information about the most recent failure."""
        return self._state.failure_info

    # Backwards compatibility
    get_failure_info = failure_info

    def set_response(self, value: Any) -> None:
        if self.current_stage is not PipelineStage.DELIVER:
            raise PluginContextError(
                f"set_response may only be called in DELIVER stage, not {self.current_stage}"
            )
        self._state.response = value
