from datetime import datetime

from entity.core.state import ConversationEntry, PipelineState
from entity.core.state_utils import (
    clear_temp_thoughts,
    get_stage_result,
    get_temp_thought,
    last_assistant_message,
    last_user_message,
)


def _make_state() -> PipelineState:
    return PipelineState(
        conversation=[
            ConversationEntry("hi", "user", datetime.now()),
            ConversationEntry("there", "assistant", datetime.now()),
        ],
        stage_results={"x": 1},
        temporary_thoughts={"y": 2},
    )


def test_last_user_message() -> None:
    state = _make_state()
    assert last_user_message(state) == "hi"


def test_last_assistant_message() -> None:
    state = _make_state()
    assert last_assistant_message(state) == "there"


def test_stage_and_temp_access() -> None:
    state = _make_state()
    assert get_stage_result(state, "x") == 1
    assert get_temp_thought(state, "y") == 2
    clear_temp_thoughts(state)
    assert get_temp_thought(state, "y") is None
