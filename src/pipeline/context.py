from __future__ import annotations

"""Runtime context passed to plugins during pipeline execution."""

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from .registries import SystemRegistries
from .stages import PipelineStage
from .state import ConversationEntry, FailureInfo, LLMResponse, PipelineState, ToolCall


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

    def _get_state(self) -> PipelineState:
        """Return the underlying :class:`PipelineState`."""
        return self.__state

    # --- Metrics helpers -------------------------------------------------
    def record_plugin_duration(self, plugin: str, duration: float) -> None:
        """Record how long ``plugin`` took to run."""
        self._get_state().metrics.record_plugin_duration(
            plugin, str(self.current_stage), duration
        )

    def record_llm_call(self, plugin: str, purpose: str) -> None:
        """Increment LLM call count for ``plugin`` and ``purpose``."""
        self._get_state().metrics.record_llm_call(
            plugin, str(self.current_stage), purpose
        )

    def record_llm_duration(self, plugin: str, duration: float) -> None:
        """Record the time spent waiting on the LLM."""
        self._get_state().metrics.record_llm_duration(
            plugin, str(self.current_stage), duration
        )

    def record_tool_execution(
        self, tool_name: str, result_key: str, source: str
    ) -> None:
        """Log execution of ``tool_name`` for observability."""
        self._get_state().metrics.record_tool_execution(
            tool_name,
            str(self.current_stage),
            self.pipeline_id,
            result_key,
            source,
        )

    def record_tool_error(self, tool_name: str, error: str) -> None:
        """Record a tool failure for monitoring."""
        self._get_state().metrics.record_tool_error(
            tool_name, str(self.current_stage), self.pipeline_id, error
        )

    # --------------------------------------------------------------------

    @property
    def pipeline_id(self) -> str:
        """Unique identifier for the current pipeline run."""
        return self._get_state().pipeline_id

    @property
    def current_stage(self) -> Optional[PipelineStage]:
        """Stage currently being executed."""
        return self._get_state().current_stage

    def get_resource(self, name: str) -> Any:
        """Return a shared resource plugin registered as ``name``."""
        return self._registries.resources.get(name)

    @property
    def message(self) -> str:
        """Return the latest user message."""
        for entry in reversed(self._get_state().conversation):
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
            result_key = (
                f"{tool_name}_result_{len(self._get_state().pending_tool_calls)}"
            )
        self._get_state().pending_tool_calls.append(
            ToolCall(name=tool_name, params=params, result_key=result_key)
        )
        return result_key

    def add_conversation_entry(
        self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append a new conversation ``entry`` to the history."""
        self._get_state().conversation.append(
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
        state = self._get_state()
        history = state.conversation if last_n is None else state.conversation[-last_n:]
        return [deepcopy(entry) for entry in history]

    def set_response(self, response: Any) -> None:
        """Set the pipeline's final ``response`` if not already set."""
        state = self._get_state()
        if state.response is not None:
            raise ValueError("Response already set")
        state.response = response

    def has_response(self) -> bool:
        """Return ``True`` if a response has been provided."""
        return self._get_state().response is not None

    def set_stage_result(self, key: str, value: Any) -> None:
        """Store intermediate ``value`` for the current stage under ``key``."""
        state = self._get_state()
        if key in state.stage_results:
            raise ValueError(f"Stage result '{key}' already set")
        state.stage_results[key] = value

    def get_stage_result(self, key: str) -> Any:
        """Retrieve a stage result stored with :meth:`set_stage_result`."""
        if key not in self._get_state().stage_results:
            raise KeyError(key)
        return self._get_state().stage_results[key]

    def has_stage_result(self, key: str) -> bool:
        """Return ``True`` if ``key`` exists in stage results."""
        return key in self._get_state().stage_results

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Return arbitrary metadata value previously stored."""
        return self._get_state().metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Store arbitrary metadata associated with the pipeline."""
        self._get_state().metadata[key] = value

    def add_failure(self, info: Any) -> None:
        """Attach failure ``info`` to the pipeline state."""
        self._get_state().failure_info = info

    def get_failure_info(self) -> FailureInfo | None:
        """Return any failure recorded during execution."""
        return self._get_state().failure_info


class SimpleContext(PluginContext):
    """Convenience context with helper methods for simple plugins."""

    @property
    def message(self) -> str:
        """Return the latest user message."""
        for entry in reversed(self._get_state().conversation):
            if entry.role == "user":
                return entry.content
        return ""

    @property
    def user(self) -> str:
        """User identifier from metadata."""
        return self._get_state().metadata.get("user", "user")

    @property
    def location(self) -> Optional[str]:
        """Return location metadata if available."""
        return self._get_state().metadata.get("location")

    def say(self, message: str) -> None:
        """Convenience wrapper around :meth:`set_response`."""
        self.set_response(message)

    def think(self, thought: str) -> None:
        """Record an internal ``thought`` message."""
        self.add_conversation_entry(
            content=thought,
            role="system",
            metadata={"type": "thought"},
        )

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve metadata value by ``key``."""
        return self.get_metadata(key, default)

    def remember(self, key: str, value: Any) -> None:
        """Persist a metadata ``value`` for later recall."""
        self.set_metadata(key, value)

    async def use_tool(self, tool_name: str, **params: Any) -> Any:
        """Execute a tool and wait for its result."""
        result_key = self.execute_tool(tool_name, params)
        return await self._wait_for_tool_result(result_key)

    async def _wait_for_tool_result(self, result_key: str) -> Any:
        """Wait for a queued tool call to finish and return its result."""
        state = self._get_state()
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
            try:
                if hasattr(tool, "execute_function_with_retry"):
                    result = await tool.execute_function_with_retry(call.params)
                elif hasattr(tool, "execute_function"):
                    result = await tool.execute_function(call.params)
                else:
                    func = getattr(tool, "run", None)
                    if func is None:
                        raise RuntimeError("Tool lacks execution method")
                    if asyncio.iscoroutinefunction(func):
                        result = await func(call.params)
                    else:
                        result = func(call.params)
                self.set_stage_result(call.result_key, result)
                self.record_tool_execution(call.name, call.result_key, call.source)
            except Exception as exc:
                result = f"Error: {exc}"
                self.set_stage_result(call.result_key, result)
                self.record_tool_error(call.name, str(exc))
            state.pending_tool_calls.remove(call)
        return self.get_stage_result(result_key)

    async def ask_llm(self, prompt: str) -> str:
        """Send ``prompt`` to the configured LLM and return its reply."""
        llm = self.get_resource("llm")
        if llm is None:
            raise RuntimeError("LLM resource 'llm' not available")

        self.record_llm_call("SimpleContext", "ask_llm")
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
            "SimpleContext", asyncio.get_event_loop().time() - start
        )

        if isinstance(response, LLMResponse):
            return response.content
        return str(response)

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
