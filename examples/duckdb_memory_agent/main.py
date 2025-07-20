import asyncio
import json
from datetime import datetime
from typing import Any, List

import sys
from pathlib import Path

import duckdb

# Ensure this example can find the entity package when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from entity import agent
from entity.plugins.base import PromptPlugin, ResourcePlugin
from entity.core.context import PluginContext
from entity.core.state import ConversationEntry
from entity.core.stages import PipelineStage


class DuckDBMemory(ResourcePlugin):
    """Simple DuckDB-backed memory."""

    name = "memory"
    stages: list[str] = []

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config or {})
        path = self.config.get("path", "agent.duckdb")
        self._conn = duckdb.connect(path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS history (conversation_id TEXT, role TEXT, content TEXT, timestamp TEXT)"
        )

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - resource
        return None

    def remember(self, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO kv VALUES (?, ?)",
            (key, json.dumps(value)),
        )

    def get(self, key: str, default: Any | None = None) -> Any:
        row = self._conn.execute(
            "SELECT value FROM kv WHERE key = ?",
            (key,),
        ).fetchone()
        return json.loads(row[0]) if row else default

    def clear(self) -> None:
        self._conn.execute("DELETE FROM kv")

    async def save_conversation(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        self._conn.execute(
            "DELETE FROM history WHERE conversation_id = ?",
            (conversation_id,),
        )
        for entry in history:
            self._conn.execute(
                "INSERT INTO history VALUES (?, ?, ?, ?)",
                (
                    conversation_id,
                    entry.role,
                    entry.content,
                    entry.timestamp.isoformat(),
                ),
            )

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        rows = self._conn.execute(
            "SELECT role, content, timestamp FROM history WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()
        return [
            ConversationEntry(
                role=row[0], content=row[1], timestamp=datetime.fromisoformat(row[2])
            )
            for row in rows
        ]


class IncrementPrompt(PromptPlugin):
    """Increment a counter stored in memory."""

    stages = [PipelineStage.OUTPUT]
    dependencies = ["memory"]

    async def _execute_impl(self, context: PluginContext) -> None:
        count = await context.recall("count", 0) + 1
        await context.remember("count", count)
        context.say(f"Count: {count}")


async def main() -> None:
    agent.builder.resource_registry.register(
        "memory", DuckDBMemory, {"path": "agent.duckdb"}, layer=3
    )
    await agent.add_plugin(IncrementPrompt({}))

    first = await agent.handle("hi")
    second = await agent.handle("again")

    print(first)
    print(second)


if __name__ == "__main__":
    asyncio.run(main())
