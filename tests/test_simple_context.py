from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginRegistry,
    ResourceRegistry,
    SimpleContext,
    SystemRegistries,
    ToolRegistry,
)


def make_context():
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="test",
        metrics=MetricsCollector(),
    )
    regs = SystemRegistries(ResourceRegistry(), ToolRegistry(), PluginRegistry())
    return SimpleContext(state, regs)


def test_simple_context_methods():
    ctx = make_context()
    ctx.say("hello")
    assert ctx._state.response == "hello"

    ctx.remember("foo", "bar")
    assert ctx.recall("foo") == "bar"
    assert ctx.recall("missing", 1) == 1

import asyncio
from datetime import datetime

from pipeline import (ConversationEntry, LLMResponse, PipelineState,
                      PluginRegistry, ResourceRegistry, SimpleContext,
                      SystemRegistries, ToolRegistry)


class EchoLLM:
    async def generate(self, prompt: str):
        return LLMResponse(content=f"echo:{prompt}")


class DoubleTool:
    async def execute_function(self, params):
        return params["n"] * 2


def make_context(message: str = "hi", **metadata):
    state = PipelineState(
        conversation=[
            ConversationEntry(content=message, role="user", timestamp=datetime.now())
        ],
        metadata=metadata,
        pipeline_id="1",
    )
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), PluginRegistry())
    return state, SimpleContext(state, registries)


def test_think_adds_entry():
    state, ctx = make_context()
    ctx.think("processing")
    assert state.conversation[-1].content == "processing"
    assert state.conversation[-1].role == "system"


def test_use_tool_executes_and_returns_result():
    state, ctx = make_context()
    ctx._registries.tools.add("double", DoubleTool())
    result = asyncio.run(ctx.use_tool("double", n=3))
    assert result == 6
    assert state.stage_results


def test_ask_llm_returns_content():
    state, ctx = make_context()
    ctx._registries.resources.add("ollama", EchoLLM())
    result = asyncio.run(ctx.ask_llm("test"))
    assert result == "echo:test"


def test_calculate_uses_calculator():
    state, ctx = make_context()
    ctx._registries.tools.add("calculator", DoubleTool())
    result = asyncio.run(ctx.calculate("unused"))
    assert result is not None


def test_is_question_and_contains_and_location():
    state, ctx = make_context("Where are you?", location="Mars")
    assert ctx.is_question()
    assert ctx.contains("where")
    assert ctx.location == "Mars"
