from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, List
from pathlib import Path
import sys

base = Path(__file__).resolve().parents[2]
sys.path.append(str(base / "src"))
sys.path.append(str(base))

import duckdb

from entity.core.plugins import PromptPlugin, ResourcePlugin
from entity.core.context import PluginContext
from entity.core.state import ConversationEntry
from entity.pipeline.stages import PipelineStage
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.pipeline.pipeline import execute_pipeline, generate_pipeline_id
from entity.pipeline.state import PipelineState


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
            "CREATE TABLE IF NOT EXISTS history ("
            "conversation_id TEXT, role TEXT, content TEXT, timestamp TEXT)"
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
            "SELECT role, content, timestamp FROM history WHERE conversation_id = ? "
            "ORDER BY timestamp",
            (conversation_id,),
        ).fetchall()
        return [
            ConversationEntry(
                role=row[0],
                content=row[1],
                timestamp=datetime.fromisoformat(row[2]),
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
    resources = ResourceContainer()
    resources.register("memory", DuckDBMemory, {"path": "agent.duckdb"})
    await resources.build_all()

    plugins = PluginRegistry()
    await plugins.register_plugin_for_stage(
        IncrementPrompt({}), PipelineStage.OUTPUT, "increment"
    )

    caps = SystemRegistries(resources=resources, tools=ToolRegistry(), plugins=plugins)

    state = PipelineState(
        conversation=[
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ],
        pipeline_id=generate_pipeline_id(),
    )
    first = await execute_pipeline("hi", caps, state=state)

    state2 = PipelineState(
        conversation=[
            ConversationEntry(content="again", role="user", timestamp=datetime.now())
        ],
        pipeline_id=generate_pipeline_id(),
    )
    second = await execute_pipeline("again", caps, state=state2)

    print(first)
    print(second)


if __name__ == "__main__":
    asyncio.run(main())
