import asyncio
from datetime import datetime

from entity.core.resources.container import ResourceContainer
from pipeline import (
    ConversationEntry,
    PipelineState,
    PluginContext,
    PluginRegistry,
    SystemRegistries,
    ToolRegistry,
)
from user_plugins.prompts.intent_classifier import IntentClassifierPrompt


class FakeLLM:
    async def generate(self, prompt: str):
        return "greeting"


def make_context(llm: FakeLLM):
    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id="1",
    )
    resources = ResourceContainer()
    asyncio.run(resources.add("llm", llm))
    capabilities = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, capabilities)


def test_intent_classifier_success():
    state, ctx = make_context(FakeLLM())
    plugin = IntentClassifierPrompt({"confidence_threshold": 0.5})

    asyncio.run(plugin.execute(ctx))

    assert ctx.recall("intent") == "greeting"


def test_intent_classifier_validate_error():
    result = IntentClassifierPrompt.validate_config({"confidence_threshold": 2})
    assert not result.success
