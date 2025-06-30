from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from .registries import SystemRegistries
from .stages import PipelineStage
from .state import ConversationEntry, LLMResponse, PipelineState, ToolCall


class PluginContext:
    """Rich state container enabling **Structured Communication (14)**."""

    def __init__(self, state: PipelineState, registries: SystemRegistries) -> None:
        self._state = state
        self._registries = registries

    @property
    def pipeline_id(self) -> str:
        return self._state.pipeline_id

    @property
    def current_stage(self) -> Optional[PipelineStage]:
        return self._state.current_stage

    def get_resource(self, name: str) -> Any:
        return self._registries.resources.get(name)

    @property
    def message(self) -> str:
        for entry in reversed(self._state.conversation):
            if entry.role == "user":
                return entry.content
        return ""

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

        self._state.metrics.record_llm_call(
            "SimpleContext", str(self.current_stage), "ask_llm"
        )

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
