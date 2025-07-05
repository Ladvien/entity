from __future__ import annotations

"""Runtime context passed to plugins during pipeline execution."""

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, cast

if TYPE_CHECKING:  # pragma: no cover
    from interfaces.resources import LLM
else:  # pragma: no cover - runtime type reference
    from interfaces.resources import LLM

from registry import SystemRegistries

from .metrics import MetricsCollector
from .stages import PipelineStage
from .state import ConversationEntry, FailureInfo, LLMResponse, PipelineState, ToolCall
from .tools.base import RetryOptions
from .tools.execution import execute_tool


class PluginContext:
    """Object exposing pipeline state and utilities to plugins."""

    def __init__(self, state: PipelineState, registries: SystemRegistries) -> None:
        """Initialize context with immutable ``state`` and ``registries``."""

        # store state privately to discourage direct access from plugins
        self.__state = state
        self._registries = registries

    # do not allow external code to read _state
    @property
    def _state(self) -> PipelineState:  # pragma: no cover - defensive measure
        raise AttributeError("Direct PipelineState access is not allowed")

    # --- Metrics helpers -------------------------------------------------
    def record_plugin_duration(self, plugin: str, duration: float) -> None:
        """Record how long ``plugin`` took to run."""
        self.__state.metrics.record_plugin_duration(
            plugin, str(self.current_stage), duration
        )

    def record_llm_call(self, plugin: str, purpose: str) -> None:
        """Increment LLM call count for ``plugin`` and ``purpose``."""
        self.__state.metrics.record_llm_call(plugin, str(self.current_stage), purpose)

    def record_llm_duration(self, plugin: str, duration: float) -> None:
        """Record the time spent waiting on the LLM."""
        self.__state.metrics.record_llm_duration(
            plugin, str(self.current_stage), duration
        )

    def record_tool_execution(
        self, tool_name: str, result_key: str, source: str
    ) -> None:
        """Log execution of ``tool_name`` for observability."""
        self.__state.metrics.record_tool_execution(
            tool_name,
            str(self.current_stage),
            self.pipeline_id,
            result_key,
            source,
        )

    def record_tool_error(self, tool_name: str, error: str) -> None:
        """Record a tool failure for monitoring."""
        self.__state.metrics.record_tool_error(
            tool_name, str(self.current_stage), self.pipeline_id, error
        )

    # --------------------------------------------------------------------

    @property
    def metrics(self) -> MetricsCollector:
        """Return the metrics collector for this pipeline."""
        return self.__state.metrics

    @property
    def pipeline_id(self) -> str:
        """Unique identifier for the current pipeline run."""
        return self.__state.pipeline_id

    @property
    def request_id(self) -> str:
        """Correlation identifier for logging."""

        return self.__state.pipeline_id

    @property
    def current_stage(self) -> Optional[PipelineStage]:
        """Stage currently being executed."""
        return self.__state.current_stage

    def get_resource(self, name: str) -> Any:
        """Return a shared resource plugin registered as ``name``."""
        return self._registries.resources.get(name)

    def get_llm(self) -> LLM:
        """Return the configured LLM resource.

        Raises:
            RuntimeError: If no ``"llm"`` resource is found.
        """
        llm = self.get_resource("llm")
        if llm is None:
            raise RuntimeError(
                "No LLM resource configured. Add 'llm' to resources section."
            )
        return cast(LLM, llm)

    @property
    def message(self) -> str:
        """Return the latest user message."""
        for entry in reversed(self.__state.conversation):
            if entry.role == "user":
                return entry.content
        return ""

    def execute_tool(
        self, tool_name: str, params: Dict[str, Any], result_key: Optional[str] = None
    ) -> str:
        """Queue execution of ``tool_name`` with ``params``.

        Returns the key where the result will be stored.
        """
        tool = self._registries.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        if result_key is None:
            result_key = f"{tool_name}_result_{len(self.__state.pending_tool_calls)}"
        self.__state.pending_tool_calls.append(
            ToolCall(name=tool_name, params=params, result_key=result_key)
        )
        return result_key

    def add_conversation_entry(
        self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append a new conversation ``entry`` to the history."""
        self.__state.conversation.append(
            ConversationEntry(
                content=content,
                role=role,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )
        )

    def get_conversation_history(
        self, last_n: Optional[int] = None
    ) -> List[ConversationEntry]:
        """Return conversation history, optionally limited to ``last_n`` entries."""
        state = self.__state
        history = state.conversation if last_n is None else state.conversation[-last_n:]
        return [deepcopy(entry) for entry in history]

    def replace_conversation_history(
        self, new_history: List[ConversationEntry]
    ) -> None:
        """Replace entire conversation history with ``new_history``."""
        self.__state.conversation = new_history

    def set_response(self, response: Any) -> None:
        """Set the pipeline's final ``response`` if not already set."""
        state = self.__state
        if state.response is not None:
            raise ValueError("Response already set")
        state.response = response

    def update_response(self, updater: Callable[[Any], Any]) -> None:
        """Update ``response`` using ``updater`` if a response exists."""
        if self.__state.response is not None:
            self.__state.response = updater(self.__state.response)

    def has_response(self) -> bool:
        """Return ``True`` if a response has been provided."""
        return self.__state.response is not None

    def set_stage_result(self, key: str, value: Any) -> None:
        """Store intermediate ``value`` for the current stage under ``key``."""
        state = self.__state
        if key in state.stage_results:
            raise ValueError(f"Stage result '{key}' already set")
        state.stage_results[key] = value

    def get_stage_result(self, key: str) -> Any:
        """Retrieve a stage result stored with :meth:`set_stage_result`."""
        if key not in self.__state.stage_results:
            raise KeyError(key)
        return self.__state.stage_results[key]

    def has_stage_result(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in stage results."""
        return key in self.__state.stage_results

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Return arbitrary metadata value previously stored."""
        return self.__state.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Store arbitrary metadata associated with the pipeline."""
        self.__state.metadata[key] = value

    def add_failure(self, info: Any) -> None:
        """Attach failure ``info`` to the pipeline state."""
        self.__state.failure_info = info

    def get_failure_info(self) -> FailureInfo | None:
        """Return any failure recorded during execution."""
        return self.__state.failure_info

    # --- Stage control ---------------------------------------------------
    def set_current_stage(self, stage: PipelineStage) -> None:
        """Update the pipeline's current stage (testing and internal use)."""
        self.__state.current_stage = stage

    # --- Convenience helpers --------------------------------------------
    @property
    def user(self) -> str:
        """Return the user identifier from metadata."""
        return self.__state.metadata.get("user", "user")

    @property
    def location(self) -> Optional[str]:
        """Return location metadata if available."""
        return self.__state.metadata.get("location")

    def say(self, message: str) -> None:
        """Shortcut for :meth:`set_response`."""
        self.set_response(message)

    def think(self, thought: str) -> None:
        """Record an internal thought message."""
        self.add_conversation_entry(
            content=thought,
            role="system",
            metadata={"type": "thought"},
        )

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from pipeline metadata."""
        return self.get_metadata(key, default)

    def remember(self, key: str, value: Any) -> None:
        """Persist a value in pipeline metadata."""
        self.set_metadata(key, value)

    async def use_tool(self, tool_name: str, **params: Any) -> Any:
        """Execute a tool and wait for its result."""
        result_key = self.execute_tool(tool_name, params)
        return await self._wait_for_tool_result(result_key)

    async def _wait_for_tool_result(self, result_key: str) -> Any:
        """Wait for a queued tool call to finish and return its result."""
        state = self.__state
        if result_key not in state.stage_results:
            call = next(
                (c for c in state.pending_tool_calls if c.result_key == result_key),
                None,
            )
            if call is None:
                raise KeyError(result_key)
            tool = self._registries.tools.get(call.name)
            if not tool:
                result = f"Error: tool {call.name} not found"
                self.set_stage_result(call.result_key, result)
                state.pending_tool_calls.remove(call)
                return result
            tool = cast(Any, tool)
            options = RetryOptions(
                max_retries=getattr(tool, "max_retries", 1),
                delay=getattr(tool, "retry_delay", 1.0),
            )
            try:
                result = await execute_tool(tool, call, state, options)
                self.set_stage_result(call.result_key, result)
                self.record_tool_execution(call.name, call.result_key, call.source)
            except Exception as exc:  # noqa: BLE001
                result = f"Error: {exc}"
                self.set_stage_result(call.result_key, result)
                self.record_tool_error(call.name, str(exc))
            state.pending_tool_calls.remove(call)
        return self.get_stage_result(result_key)

    async def ask_llm(self, prompt: str) -> str:
        """Send ``prompt`` to the configured LLM and return its reply."""
        llm = self.get_llm()
        if llm is None:
            raise RuntimeError("LLM resource not available")

        self.record_llm_call("PluginContext", "ask_llm")
        start = asyncio.get_event_loop().time()

        if hasattr(llm, "generate"):
            response = await llm.generate(prompt)
        else:
            func = getattr(llm, "__call__", None)
            if func is None:
                raise RuntimeError("LLM resource is not callable")
            if asyncio.iscoroutinefunction(func):
                response = await func(prompt)
            else:
                response = func(prompt)

        self.record_llm_duration(
            "PluginContext", asyncio.get_event_loop().time() - start
        )

        if isinstance(response, LLMResponse):
            return response.content
        return str(response)

    async def stream_llm(self, prompt: str):
        """Stream LLM output using server-sent events."""
        llm = self.get_llm()
        self.record_llm_call("PluginContext", "stream_llm")
        start = asyncio.get_event_loop().time()
        async for chunk in llm.stream(prompt):
            yield chunk
        self.record_llm_duration(
            "PluginContext", asyncio.get_event_loop().time() - start
        )

    async def calculate(self, expression: str) -> Any:
        """Evaluate an arithmetic ``expression`` using the calculator tool."""
        return await self.use_tool("calculator", expression=expression)

    def is_question(self) -> bool:
        """Return ``True`` if the user message ends with a question mark."""
        return self.message.strip().endswith("?")

    def contains(self, *keywords: str) -> bool:
        """Return ``True`` if any ``keywords`` appear in the user message."""
        msg_lower = self.message.lower()
        return any(keyword.lower() in msg_lower for keyword in keywords)


class SimpleContext(PluginContext):
    """Beginner-friendly wrapper around :class:`PluginContext`."""

    pass
