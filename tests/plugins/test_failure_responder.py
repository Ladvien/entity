import pytest

from entity.pipeline.errors import PluginContextError
from entity.core.stages import PipelineStage
from plugin_library.failure import ErrorFormatter
from plugin_library.responders import FailureResponder
from tests.utils import make_async_context


@pytest.mark.asyncio
async def test_say_disallowed_in_error_stage() -> None:
    ctx = await make_async_context(stage=PipelineStage.ERROR)
    with pytest.raises(PluginContextError):
        ctx.say("nope")


@pytest.mark.asyncio
async def test_formatter_and_responder_flow() -> None:
    state_ctx = await make_async_context(stage=PipelineStage.ERROR)
    await state_ctx.think("failure_response", {"error": "boom"})
    formatter = ErrorFormatter({})
    responder = FailureResponder({})
    await formatter.execute(state_ctx)
    # switch to OUTPUT stage for responder
    state_ctx.set_current_stage(PipelineStage.OUTPUT)
    await responder.execute(state_ctx)
    assert state_ctx._state.response == {"error": "boom"}
