import asyncio
import os
from datetime import datetime
from pathlib import Path

import pytest

from config.environment import load_env
from pipeline.plugins.resources.postgres import PostgresResource
from pipeline.state import ConversationEntry

load_env(Path(__file__).resolve().parents[2] / ".env")

CONN = {
    "host": os.environ["DB_HOST"],
    "port": 5432,
    "name": os.environ["DB_NAME"],
    "username": os.environ["DB_USERNAME"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "pool_min_size": 1,
    "pool_max_size": 2,
}


@pytest.mark.integration
def test_save_and_load_history():
    async def run():
        resource = PostgresResource(CONN)
        try:
            await resource.initialize()
        except OSError as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
        await resource.execute("DROP TABLE IF EXISTS test_history")
        await resource.execute(
            "CREATE TABLE test_history ("
            "conversation_id text, role text, content text, "
            "metadata jsonb, timestamp timestamptz)"
        )
        entry = ConversationEntry(
            content="hello", role="user", timestamp=datetime.now()
        )
        await resource.execute(
            "INSERT INTO test_history (conversation_id, role, content, metadata, timestamp)"
            " VALUES ($1, $2, $3, $4, $5)",
            "conv1",
            entry.role,
            entry.content,
            "{}",
            entry.timestamp,
        )
        rows = await resource.fetch(
            "SELECT role, content, metadata, timestamp FROM test_history WHERE conversation_id=$1",
            "conv1",
        )
        loaded = [
            ConversationEntry(
                role=r["role"],
                content=r["content"],
                metadata={},
                timestamp=r["timestamp"],
            )
            for r in rows
        ]
        await resource.shutdown()
        return loaded

    history = asyncio.run(run())
    assert len(history) == 1
    assert history[0].content == "hello"
