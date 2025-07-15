import shutil
import asyncio
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


@pytest.fixture()
def prepared_postgres(postgresql_proc, request):
    """Ensure the test database exists and clean it up afterwards."""
    from pytest_postgresql.janitor import DatabaseJanitor

    janitor = DatabaseJanitor(
        user=postgresql_proc.user,
        host=postgresql_proc.host,
        port=postgresql_proc.port,
        dbname=postgresql_proc.dbname,
        template_dbname=postgresql_proc.template_dbname,
        version=postgresql_proc.version,
        password=postgresql_proc.password,
    )

    janitor.init()

    async def create_extension() -> None:
        conn = await asyncpg.connect(
            user=postgresql_proc.user,
            password=postgresql_proc.password,
            database=postgresql_proc.dbname,
            host=postgresql_proc.host,
            port=postgresql_proc.port,
        )
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.close()

    asyncio.run(create_extension())

    def drop_db():
        janitor.drop()

    request.addfinalizer(drop_db)
    return postgresql_proc


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
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{prepared_postgres.user}:{prepared_postgres.password}@"
        f"{prepared_postgres.host}:{prepared_postgres.port}/{prepared_postgres.dbname}"
    )
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
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{prepared_postgres.user}:{prepared_postgres.password}@"
        f"{prepared_postgres.host}:{prepared_postgres.port}/{prepared_postgres.dbname}"
    )
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
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{prepared_postgres.user}:{prepared_postgres.password}@"
        f"{prepared_postgres.host}:{prepared_postgres.port}/{prepared_postgres.dbname}"
    )
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
    if shutil.which("pg_ctl") is None:
        pytest.skip("pg_ctl not installed")
    dsn = (
        f"postgresql://{prepared_postgres.user}:{prepared_postgres.password}@"
        f"{prepared_postgres.host}:{prepared_postgres.port}/{prepared_postgres.dbname}"
    )
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
