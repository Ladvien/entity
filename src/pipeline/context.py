from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .state import ConversationEntry, PipelineState, ToolCall
from .stages import PipelineStage


@dataclass
class SystemRegistries:
    resources: "ResourceRegistry"
    tools: "ToolRegistry"
    plugins: "PluginRegistry"


class PluginContext:
    """Clean interface provided to plugins during execution."""

    def __init__(self, state: PipelineState, registries: SystemRegistries):
        self._state = state
        self._registries = registries

    @property
    def pipeline_id(self) -> str:
        return self._state.pipeline_id

    @property
    def current_stage(self) -> PipelineStage:
        return self._state.current_stage

    # Resource access
    def get_resource(self, name: str):
        return self._registries.resources.get(name)

    # Tool execution
    def execute_tool(self, tool_name: str, params: Dict[str, Any], result_key: str | None = None) -> str:
        tool = self._registries.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        if result_key is None:
            result_key = f"{tool_name}_result_{len(self._state.pending_tool_calls)}"
        call = ToolCall(name=tool_name, params=params, result_key=result_key, source="direct_execution")
        self._state.pending_tool_calls.append(call)
        return result_key

    # Conversation access
    def add_conversation_entry(self, content: str, role: str, metadata: Dict[str, Any] | None = None) -> None:
        entry = ConversationEntry(content=content, role=role, timestamp=datetime.now(), metadata=metadata or {})
        self._state.conversation.append(entry)

    def get_conversation_history(self, last_n: int | None = None) -> List[ConversationEntry]:
        if last_n is None:
            return self._state.conversation.copy()
        return self._state.conversation[-last_n:].copy()

    # Response control
    def set_response(self, response: Any) -> None:
        if self._state.response is not None:
            raise ValueError("Response already set")
        self._state.response = response

    def has_response(self) -> bool:
        return self._state.response is not None

    # Stage results
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

    # Metadata
    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._state.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self._state.metadata[key] = value

    # Error handling
    def add_failure(self, failure: "FailureInfo") -> None:
        self._state.failure_info = failure
