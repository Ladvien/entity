import asyncio
from datetime import datetime

from user_plugins.prompts.react_prompt import ReActPrompt
from user_plugins.tools.calculator_tool import CalculatorTool

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


def make_context(llm: FakeLLM):
    state = PipelineState(
        conversation=[
            ConversationEntry(
                content="What is 2+2?", role="user", timestamp=datetime.now()
            )
        ],
        pipeline_id="1",
        metrics=MetricsCollector(),
    )
    resources = ResourceContainer()
    tools = ToolRegistry()
    plugins = PluginRegistry()
    asyncio.run(resources.add("llm", llm))

    calculator = CalculatorTool()
    asyncio.run(tools.add("calculator_tool", calculator))

    registries = SystemRegistries(resources, tools, plugins)
    return state, PluginContext(state, registries)


def test_react_prompt_multiple_steps_and_tool_call():
    llm = FakeLLM(
        [
            "I should calculate",  # thought 0
            "Action: calculate 2+2",  # action 0
            "Now I know",  # thought 1
            "Final Answer: 4",  # action 1
        ]
    )
    state, ctx = make_context(llm)
    plugin = ReActPrompt({"max_steps": 3})

    asyncio.run(plugin.execute(ctx))

    assert state.response == "4"
    assert len(state.pending_tool_calls) == 1
    call = state.pending_tool_calls[0]
    assert call.name == "calculator_tool"
    assert call.params["expression"] == "2+2"
    assistant_entries = [e for e in state.conversation if e.role == "assistant"]
    assert len(assistant_entries) == 3
