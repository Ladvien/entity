from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from .pipeline import SystemRegistries

from .stages import PipelineStage


@dataclass
class ConversationEntry:
    content: str
    role: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    name: str
    params: Dict[str, Any]
    result_key: str
    source: str = "direct_execution"


@dataclass
class LLMResponse:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureInfo:
    stage: str
    plugin_name: str
    error_type: str
    error_message: str
    original_exception: Exception
    context_snapshot: Dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {}

    def record_plugin_duration(self, plugin: str, stage: str, duration: float) -> None:
        key = f"plugin_duration.{plugin}.{stage}"
        self.metrics[key] = duration

    def record_tool_execution(
        self, tool_name: str, stage: str, pipeline_id: str, result_key: str, source: str
    ) -> None:
        key = f"tool_exec.{tool_name}.{stage}.{pipeline_id}"
        self.metrics[key] = {"result_key": result_key, "source": source}

    def record_tool_error(
        self, tool_name: str, stage: str, pipeline_id: str, error: str
    ) -> None:
        key = f"tool_error.{tool_name}.{stage}.{pipeline_id}"
        self.metrics[key] = error

    def record_llm_call(self, plugin: str, stage: str, purpose: str) -> None:
        key = f"llm_call.{plugin}.{stage}.{purpose}"
        self.metrics[key] = self.metrics.get(key, 0) + 1


@dataclass
class PipelineState:
    conversation: List[ConversationEntry]
    response: Any = None
    prompt: str = ""
    stage_results: Dict[str, Any] = field(default_factory=dict)
    pending_tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    pipeline_id: str = ""
    current_stage: Optional[PipelineStage] = None
    metrics: MetricsCollector = field(default_factory=MetricsCollector)
    failure_info: Optional[FailureInfo] = None


class PluginContext:
    def __init__(self, state: PipelineState, registries: "SystemRegistries") -> None:
        self._state = state
        self._registries = registries

    @property
    def pipeline_id(self) -> str:
        return self._state.pipeline_id

    @property
    def current_stage(self) -> PipelineStage:
        return self._state.current_stage

    def get_resource(self, name: str) -> Any:
        return self._registries.resources.get(name)

    def execute_tool(
        self, tool_name: str, params: Dict[str, Any], result_key: Optional[str] = None
    ) -> str:
        tool = self._registries.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        if result_key is None:
            result_key = f"{tool_name}_result_{len(self._state.pending_tool_calls)}"
        self._state.pending_tool_calls.append(
            ToolCall(name=tool_name, params=params, result_key=result_key)
        )
        return result_key

    def add_conversation_entry(
        self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self._state.conversation.append(
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
        if last_n is None:
            return list(self._state.conversation)
        return self._state.conversation[-last_n:]

    def set_response(self, response: Any) -> None:
        if self._state.response is not None:
            raise ValueError("Response already set")
        self._state.response = response

    def has_response(self) -> bool:
        return self._state.response is not None

    def set_stage_result(self, key: str, value: Any) -> None:
        if key in self._state.stage_results:
            raise ValueError(f"Stage result '{key}' already set")
        self._state.stage_results[key] = value

    def get_stage_result(self, key: str) -> Any:
        if key not in self._state.stage_results:
            raise KeyError(key)
        return self._state.stage_results[key]

    def has_stage_result(self, key: str) -> bool:
        return key in self._state.stage_results

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._state.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._state.metadata[key] = value

    def add_failure(self, info: Any) -> None:
        self._state.failure_info = info


class SimpleContext(PluginContext):
    @property
    def message(self) -> str:
        for entry in reversed(self._state.conversation):
            if entry.role == "user":
                return entry.content
        return ""

    @property
    def user(self) -> str:
        return self._state.metadata.get("user", "user")

    @property
    def location(self) -> Optional[str]:
        return self._state.metadata.get("location")

    def say(self, message: str) -> None:
        self.set_response(message)

    def think(self, thought: str) -> None:
        self.add_conversation_entry(
            content=thought,
            role="system",
            metadata={"type": "thought"},
        )

    def recall(self, key: str, default: Any = None) -> Any:
        return self.get_metadata(key, default)

    def remember(self, key: str, value: Any) -> None:
        self.set_metadata(key, value)

    async def use_tool(self, tool_name: str, **params: Any) -> Any:
        result_key = self.execute_tool(tool_name, params)
        return await self._wait_for_tool_result(result_key)

    async def _wait_for_tool_result(self, result_key: str) -> Any:
        if result_key not in self._state.stage_results:
            call = next(
                (
                    c
                    for c in self._state.pending_tool_calls
                    if c.result_key == result_key
                ),
                None,
            )
            if call is None:
                raise KeyError(result_key)
            tool = self._registries.tools.get(call.name)
            if not tool:
                result = f"Error: tool {call.name} not found"
                self.set_stage_result(call.result_key, result)
                self._state.pending_tool_calls.remove(call)
                return result
            try:
                if hasattr(tool, "execute_function_with_retry"):
                    result = await tool.execute_function_with_retry(call.params)
                elif hasattr(tool, "execute_function"):
                    result = await tool.execute_function(call.params)
                else:
                    func = getattr(tool, "run", None)
                    if asyncio.iscoroutinefunction(func):
                        result = await func(call.params)
                    else:
                        result = func(call.params)
                self.set_stage_result(call.result_key, result)
                self._state.metrics.record_tool_execution(
                    call.name,
                    str(self.current_stage),
                    self.pipeline_id,
                    call.result_key,
                    call.source,
                )
            except Exception as exc:
                result = f"Error: {exc}"
                self.set_stage_result(call.result_key, result)
                self._state.metrics.record_tool_error(
                    call.name,
                    str(self.current_stage),
                    self.pipeline_id,
                    str(exc),
                )
            self._state.pending_tool_calls.remove(call)
        return self.get_stage_result(result_key)

    async def ask_llm(self, prompt: str) -> str:
        llm = self.get_resource("ollama")
        if llm is None:
            raise RuntimeError("LLM resource 'ollama' not available")

        if hasattr(llm, "generate"):
            response = await llm.generate(prompt)
        else:
            func = getattr(llm, "__call__", None)
            if asyncio.iscoroutinefunction(func):
                response = await func(prompt)
            else:
                response = func(prompt)

        if isinstance(response, LLMResponse):
            return response.content
        return str(response)

    async def calculate(self, expression: str) -> Any:
        return await self.use_tool("calculator", expression=expression)

    def is_question(self) -> bool:
        return self.message.strip().endswith("?")

    def contains(self, *keywords: str) -> bool:
        msg_lower = self.message.lower()
        return any(keyword.lower() in msg_lower for keyword in keywords)
