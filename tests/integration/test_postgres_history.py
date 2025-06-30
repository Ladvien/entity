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
    "name": "dev_db",
    "username": os.environ["DB_USERNAME"],
    "password": os.environ.get("DB_PASSWORD", ""),
    "history_table": "test_history",
}


@pytest.mark.integration
def test_save_and_load_history():
    async def run():
        resource = PostgresResource(CONN)
        try:
            await resource.initialize()
        except OSError as exc:
            pytest.skip(f"PostgreSQL not available: {exc}")
        await resource._connection.execute("DROP TABLE IF EXISTS test_history")
        await resource._connection.execute(
            "CREATE TABLE test_history ("
            "conversation_id text, role text, content text, "
            "metadata jsonb, timestamp timestamptz)"
        )
        entries = [
            ConversationEntry(content="hello", role="user", timestamp=datetime.now())
        ]
        await resource.save_history("conv1", entries)
        loaded = await resource.load_history("conv1")
        await resource._connection.close()
        return loaded

    history = asyncio.run(run())
    assert len(history) == 1
    assert history[0].content == "hello"
