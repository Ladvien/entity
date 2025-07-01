from __future__ import annotations

from pipeline.context import PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ConversationHistorySaver(PromptPlugin):
    """Persist conversation history to the configured database."""

    dependencies = ["database", "llm"]
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context: PluginContext) -> None:
        """Save the entire conversation using the database resource."""
        db = context.get_resource("database")
        if db and hasattr(db, "save_history"):
            await db.save_history(
                context.pipeline_id, context.get_conversation_history()
            )
