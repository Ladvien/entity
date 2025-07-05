import asyncio
from datetime import datetime

from plugins.builtin.resources.duckdb_database import DuckDBDatabaseResource

from pipeline.context import ConversationEntry


def test_duckdb_history_roundtrip(tmp_path):
    async def run():
        cfg = {"path": tmp_path / "test.duckdb", "history_table": "history"}
        resource = DuckDBDatabaseResource(cfg)
        await resource.initialize()
        entry = ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        await resource.save_history("conv1", [entry])
        rows = await resource.load_history("conv1")
        await resource.shutdown()
        return rows

    history = asyncio.run(run())
    assert history and history[0].content == "hi"
