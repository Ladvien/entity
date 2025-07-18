from datetime import datetime

from entity.core.state import ConversationEntry, PipelineState


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
    assert state.last_user_message() == "hi"


def test_last_assistant_message() -> None:
    state = _make_state()
    assert state.last_assistant_message() == "there"


def test_stage_and_temp_access() -> None:
    state = _make_state()
    assert state.get_stage_result("x") == 1
    assert state.get_temp_thought("y") == 2
    state.clear_temp_thoughts()
    assert state.get_temp_thought("y") is None
