from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from entity.infrastructure import DuckDBInfrastructure
from entity.resources import Memory
from entity.resources.interfaces.duckdb_resource import DuckDBResource


@pytest.fixture()
async def memory_db(tmp_path: Path) -> Memory:
    db_path = tmp_path / "memory.duckdb"
    db_backend = DuckDBInfrastructure({"path": str(db_path)})
    await db_backend.initialize()
    async with db_backend.connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_history (conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
        )
    db = DuckDBResource({})
    db.database = db_backend
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        await db_backend.shutdown()
