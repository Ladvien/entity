from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .registries import SystemRegistries
from .stages import PipelineStage
from .state import ConversationEntry, PipelineState, ToolCall


class PluginContext:
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
