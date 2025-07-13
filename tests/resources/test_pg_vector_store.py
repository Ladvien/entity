import shutil
import pytest

if shutil.which("pg_ctl") is None:  # pragma: no cover - environment check
    pytest.skip("pg_ctl not installed", allow_module_level=True)
from datetime import datetime
from contextlib import asynccontextmanager
import asyncpg
from pgvector.asyncpg import register_vector

from entity.resources import Memory
from entity.core.state import ConversationEntry
from entity.resources.interfaces.database import DatabaseResource
from plugins.builtin.resources.pg_vector_store import PgVectorStore


class AsyncPGDatabase(DatabaseResource):
    def __init__(self, dsn: str) -> None:
        super().__init__({})
        self._dsn = dsn

    @asynccontextmanager
    async def connection(self):
        conn = await asyncpg.connect(self._dsn)
        await register_vector(conn)
        try:
            yield conn
        finally:
            await conn.close()

    def get_connection_pool(self):  # pragma: no cover - simplify
        return self._dsn


@pytest.mark.asyncio
async def test_embedding_roundtrip(postgresql_proc) -> None:
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{postgresql_proc.user}:{postgresql_proc.password}@"
        f"{postgresql_proc.host}:{postgresql_proc.port}/{postgresql_proc.dbname}"
    )
    db = AsyncPGDatabase(dsn)
    store = PgVectorStore({"table": "embeddings"})
    store.database = db
    mem = Memory({})
    mem.database = db
    mem.vector_store = store
    await mem.initialize()
    await store.initialize()

    await mem.add_embedding("hello world")
    await mem.add_embedding("goodbye world")

    results = await mem.vector_search("hello", k=1)
    assert results == ["hello world"]


@pytest.mark.asyncio
async def test_conversation_integration(postgresql_proc) -> None:
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{postgresql_proc.user}:{postgresql_proc.password}@"
        f"{postgresql_proc.host}:{postgresql_proc.port}/{postgresql_proc.dbname}"
    )
    db = AsyncPGDatabase(dsn)
    store = PgVectorStore({"table": "embeddings"})
    store.database = db
    mem = Memory({})
    mem.database = db
    mem.vector_store = store
    await mem.initialize()
    await store.initialize()

    await mem.add_conversation_entry(
        "conv",
        ConversationEntry(content="hello there", role="user", timestamp=datetime.now()),
        user_id="u",
    )
    matches = await mem.conversation_search("hello", user_id="u")
    assert len(matches) == 1
    assert matches[0]["content"] == "hello there"
