import asyncio
from datetime import datetime

from user_plugins.prompts.chain_of_thought import ChainOfThoughtPrompt

from pipeline import (ConversationEntry, MetricsCollector, PipelineState,
                      PluginContext, PluginRegistry, SystemRegistries,
                      ToolRegistry)
from pipeline.resources import ResourceContainer


class FakeLLM:
    name = "llm"

    def __init__(self, responses):
        self._responses = list(responses)

    async def generate(self, prompt: str):
        return self._responses.pop(0)


class DummyTool:
    async def execute_function(self, params):  # pragma: no cover - simple stub
        return {"analysis": params}


def make_context(llm: FakeLLM):
    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="How does this work?", role="user", timestamp=datetime.now()
            )
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceContainer()
    tools = ToolRegistry()
    plugins = PluginRegistry()
    asyncio.run(resources.add("llm", llm))
    asyncio.run(tools.add("analysis_tool", DummyTool()))
    registries = SystemRegistries(resources, tools, plugins)
    return state, PluginContext(state, registries)


def test_chain_of_thought_records_steps_and_tool_call():
    llm = FakeLLM(
        [
            "Breakdown response",  # breakdown
            "We need to calculate result",  # step 1
            "Final answer is 42",  # step 2
        ]
    )
    state, ctx = make_context(llm)
    plugin = ChainOfThoughtPrompt({"max_steps": 3})

    asyncio.run(plugin.execute(ctx))

    assistant_entries = [e for e in state.conversation if e.role == "assistant"]
    assert assistant_entries[0].content == "Problem breakdown: Breakdown response"
    assert (
        assistant_entries[1].content == "Reasoning step 1: We need to calculate result"
    )
    assert assistant_entries[2].content == "Reasoning step 2: Final answer is 42"
    assert state.stage_results["reasoning_complete"] is True
    assert state.stage_results["reasoning_steps"] == [
        "We need to calculate result",
        "Final answer is 42",
    ]
    assert len(state.pending_tool_calls) == 1
    call = state.pending_tool_calls[0]
    assert call.name == "analysis_tool"
    assert call.params["data"] == "How does this work?"
