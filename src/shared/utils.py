from src.shared.models import ChatResponse
from src.shared.agent_result import AgentResult


def agent_result_to_response(result: AgentResult) -> ChatResponse:
    return ChatResponse(
        thread_id=result.thread_id,
        timestamp=result.timestamp,
        raw_input=result.raw_input,
        raw_output=result.raw_output,
        response=result.final_response,
        tools_used=result.tools_used,
        token_count=result.token_count,
        memory_context=result.memory_context,
        intermediate_steps=result.intermediate_steps,
    )
