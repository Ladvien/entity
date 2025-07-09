from __future__ import annotations

"""Minimal plugin context objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pipeline.stages import PipelineStage
from pipeline.state import ConversationEntry, PipelineState, ToolCall
from pipeline.errors import PluginContextError


@dataclass
class ConversationEntry:
    content: str
    role: str
    metadata: Dict[str, Any] | None = None


class PluginContext:
    """Runtime context passed to plugins."""

    def __init__(self, state: PipelineState, registries: Any) -> None:
        self._state = state
        self._registries = registries
        self._store: Dict[str, Any] = {}

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
        tool = self._registries.tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return await tool.execute_function(params)

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

    # Backwards compatibility
    store = cache
    load = recall

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
        return self._memory.memory(key, default)

    def load(self, key: str, default: Any | None = None) -> Any:
        """Return ``key`` from the internal store or ``default`` when missing."""

        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        """Return ``True`` when ``key`` is stored."""

        return key in self._store

    def load(self, key: str, default: Any | None = None) -> Any:
        return self._store.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._state.metadata[key] = value

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        return self._state.metadata.get(key, default)

    def get_failure_info(self) -> Any:
        return self._state.failure_info

    def set_response(self, value: Any) -> None:
        if self.current_stage is not PipelineStage.DELIVER:
            raise PluginContextError(
                f"set_response may only be called in DELIVER stage, not {self.current_stage}"
            )
        self._state.response = value
