from pathlib import Path

import pytest

from entity.infrastructure import DuckDBInfrastructure
from entity.resources import Memory


@pytest.fixture()
async def memory_db(tmp_path: Path) -> Memory:
    db_path = tmp_path / "memory.duckdb"
    db = DuckDBInfrastructure({"path": str(db_path)})
    await db.initialize()
    async with db.connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_history (conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
        )
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        await db.shutdown()
