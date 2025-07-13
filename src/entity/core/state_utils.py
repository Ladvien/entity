from __future__ import annotations

from typing import Any, Optional

from .state import ConversationEntry, PipelineState


def _last_entry(state: PipelineState, role: str) -> Optional[ConversationEntry]:
    for entry in reversed(state.conversation):
        if entry.role == role:
            return entry
    return None


def last_user_message(state: PipelineState) -> Optional[str]:
    entry = _last_entry(state, "user")
    return entry.content if entry else None


def last_assistant_message(state: PipelineState) -> Optional[str]:
    entry = _last_entry(state, "assistant")
    return entry.content if entry else None


def get_stage_result(state: PipelineState, key: str, default: Any | None = None) -> Any:
    return state.stage_results.get(key, default)


def get_temp_thought(state: PipelineState, key: str, default: Any | None = None) -> Any:
    return state.temporary_thoughts.get(key, default)


def clear_temp_thoughts(state: PipelineState) -> None:
    state.temporary_thoughts.clear()
