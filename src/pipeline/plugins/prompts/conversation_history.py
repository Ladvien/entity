from __future__ import annotations

import json
from typing import Dict, List

from pipeline.context import ConversationEntry, PluginContext
from pipeline.plugins import PromptPlugin
from pipeline.stages import PipelineStage


class ConversationHistory(PromptPlugin):
    """Load and persist conversation history using the database resource."""

    dependencies = ["database"]
    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._schema = self.config.get("db_schema")
        self._table = self.config.get("history_table", "chat_history")

    def _table_name(self) -> str:
        return f"{self._schema + '.' if self._schema else ''}{self._table}"

    async def _execute_impl(self, context: PluginContext) -> None:
        db = context.get_resource("database")
        if db is None:
            return

        table = self._table_name()
        if context.current_stage == PipelineStage.PARSE:
            rows = await db.fetch(
                f"SELECT role, content, metadata, timestamp FROM {table} "
                "WHERE conversation_id=$1 ORDER BY timestamp",
                context.pipeline_id,
            )
            for row in rows:
                metadata = row["metadata"]
                if not isinstance(metadata, dict):
                    metadata = json.loads(metadata) if metadata else {}
                context.add_conversation_entry(
                    content=row["content"],
                    role=row["role"],
                    metadata=metadata,
                    timestamp=row["timestamp"],
                )
        else:
            history: List[ConversationEntry] = context.get_conversation_history()
            for entry in history:
                await db.execute(
                    f"INSERT INTO {table} "
                    "(conversation_id, role, content, metadata, timestamp)",
                    context.pipeline_id,
                    entry.role,
                    entry.content,
                    json.dumps(entry.metadata),
                    entry.timestamp,
                )
