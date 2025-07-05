import asyncio
from datetime import datetime

from pipeline import (
    ConversationEntry,
    MetricsCollector,
    PipelineState,
    PluginContext,
    PluginRegistry,
    ResourceRegistry,
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
        metrics=MetricsCollector(),
    )
    resources = ResourceRegistry()
    asyncio.run(resources.add("llm", llm))
    registries = SystemRegistries(resources, ToolRegistry(), PluginRegistry())
    return state, PluginContext(state, registries)


def test_intent_classifier_success():
    state, ctx = make_context(FakeLLM())
    plugin = IntentClassifierPrompt({"confidence_threshold": 0.5})

    asyncio.run(plugin.execute(ctx))

    assert state.stage_results["intent"] == "greeting"


def test_intent_classifier_validate_error():
    result = IntentClassifierPrompt.validate_config({"confidence_threshold": 2})
    assert not result.success
