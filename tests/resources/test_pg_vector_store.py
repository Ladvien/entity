import pytest
from datetime import datetime
from contextlib import asynccontextmanager
import asyncpg
from pgvector.asyncpg import register_vector

from entity.resources import Memory
from entity.core.state import ConversationEntry
from entity.resources.database import DatabaseResource
from plugins.builtin.resources.pg_vector_store import PgVectorStore


@asynccontextmanager
async def get_pg_connection(dsn):
    conn = await asyncpg.connect(dsn)
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture()
async def prepared_postgres(postgres_dsn: str):
    """Return DSN for containerized Postgres and ensure a clean state."""
    async with get_pg_connection(postgres_dsn) as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("DROP TABLE IF EXISTS memory_kv")
        await conn.execute("DROP TABLE IF EXISTS conversation_history")
        await conn.execute("DROP TABLE IF EXISTS embeddings")
    yield postgres_dsn
    async with get_pg_connection(postgres_dsn) as conn:
        await conn.execute("DROP TABLE IF EXISTS memory_kv")
        await conn.execute("DROP TABLE IF EXISTS conversation_history")
        await conn.execute("DROP TABLE IF EXISTS embeddings")


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
async def test_embedding_roundtrip(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    store = PgVectorStore({"table": "embeddings"})
    store.database = db
    mem = Memory({})
    mem.database = db
    mem.vector_store = store
    await store.initialize()
    await mem.initialize()

    await mem.add_embedding("hello world")
    await mem.add_embedding("goodbye world")

    results = await mem.vector_search("hello", k=1)
    assert results == ["hello world"]


@pytest.mark.asyncio
async def test_conversation_integration(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    store = PgVectorStore({"table": "embeddings"})
    store.database = db
    mem = Memory({})
    mem.database = db
    mem.vector_store = store
    await store.initialize()
    await mem.initialize()

    await mem.add_conversation_entry(
        "conv",
        ConversationEntry(content="hello there", role="user", timestamp=datetime.now()),
        user_id="u",
    )
    matches = await mem.conversation_search("hello", user_id="u")
    assert len(matches) == 1
    assert matches[0]["content"] == "hello there"


@pytest.mark.asyncio
async def test_asyncpg_paramstyle_insert(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    mem = Memory({})
    mem.database = db
    await mem.initialize()

    entry = ConversationEntry(
        content="asyncpg works", role="user", timestamp=datetime.now()
    )
    await mem.add_conversation_entry("conv", entry, user_id="u")
    history = await mem.load_conversation("conv", user_id="u")
    assert len(history) == 1
    assert history[0].content == "asyncpg works"


@pytest.mark.asyncio
async def test_asyncpg_search_and_load(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    mem = Memory({})
    mem.database = db
    await mem.initialize()

    await mem.add_conversation_entry(
        "conv",
        ConversationEntry(content="search me", role="user", timestamp=datetime.now()),
        user_id="u",
    )

    history = await mem.load_conversation("conv", user_id="u")
    assert [h.content for h in history] == ["search me"]

    results = await mem.conversation_search("search", user_id="u")
    assert len(results) == 1
    assert results[0]["content"] == "search me"


@pytest.mark.asyncio
async def test_asyncpg_conversation_statistics(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    mem = Memory({})
    mem.database = db
    await mem.initialize()

    now = datetime.now()
    await mem.add_conversation_entry(
        "c1", ConversationEntry("hi", "user", now), user_id="u"
    )
    await mem.add_conversation_entry(
        "c1", ConversationEntry("bye", "assistant", now), user_id="u"
    )
    await mem.add_conversation_entry(
        "c2", ConversationEntry("ping", "user", now), user_id="u"
    )

    stats = await mem.conversation_statistics("u")
    assert stats["conversations"] == 2
    assert stats["messages"] == 3


@pytest.mark.asyncio
async def test_asyncpg_save_and_load(prepared_postgres) -> None:
    dsn = prepared_postgres
    db = AsyncPGDatabase(dsn)
    mem = Memory({})
    mem.database = db
    await mem.initialize()

    entry = ConversationEntry("store me", "user", datetime.now())
    await mem.save_conversation("conv", [entry], user_id="u")
    loaded = await mem.load_conversation("conv", user_id="u")
    assert loaded == [entry]
