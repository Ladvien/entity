from __future__ import annotations

from entity.core.context import PluginContext
from entity.plugins.base import PromptPlugin
from entity.core.stages import PipelineStage


class MultiProviderResponder(PromptPlugin):
    """Combine responses from multiple LLM providers."""

    name = "multi_responder"
    dependencies = ["llm", "openai_provider", "anthropic_provider"]
    stages = [PipelineStage.THINK, PipelineStage.OUTPUT]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        if ctx.stage is PipelineStage.THINK:
            question = next(
                (e.content for e in ctx.conversation() if e.role == "user"), ""
            )
            llm = ctx.get_resource("llm")
            result = await llm.generate(question)
            await ctx.think("draft", result.content)
        else:
            draft = ctx.recall("draft", "")
            openai = ctx.get_resource("openai_provider")
            refined = await openai.generate(f"Refine the answer: {draft}")
            anthropic = ctx.get_resource("anthropic_provider")
            final = await anthropic.generate(f"Check for safety: {refined}")
            ctx.say(final.content)


class VectorStoreLogger(PromptPlugin):
    """Store final responses in the vector store."""

    name = "vector_logger"
    dependencies = ["vector_store"]
    stages = [PipelineStage.REVIEW]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        if not ctx.has_response():
            return
        store = ctx.get_resource("vector_store")
        await store.add_embedding(ctx.response)
