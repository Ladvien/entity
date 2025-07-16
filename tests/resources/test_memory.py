from datetime import datetime, timedelta

from tests.conftest import AsyncPGDatabase
import pytest

from entity.resources import Memory
from entity.resources.interfaces.vector_store import VectorStoreResource
from entity.core.state import ConversationEntry


class DummyVector(VectorStoreResource):
    def __init__(self) -> None:
        super().__init__({})
        self.entries: list[str] = []

    async def add_embedding(self, text: str) -> None:
        self.entries.append(text)

    async def query_similar(self, query: str, k: int = 5):
        return [t for t in self.entries if query in t][:k]


@pytest.fixture()
async def memory_with_vector(postgres_dsn: str) -> Memory:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = DummyVector()
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


@pytest.mark.asyncio
async def test_conversation_search_vector(memory_with_vector: Memory) -> None:
    await memory_with_vector.add_conversation_entry(
        "conv",
        ConversationEntry(content="hello world", role="user", timestamp=datetime.now()),
        user_id="user",
    )
    results = await memory_with_vector.conversation_search("hello", user_id="user")
    assert len(results) == 1
    assert results[0]["content"] == "hello world"


@pytest.mark.asyncio
async def test_conversation_search_text(memory_with_vector: Memory) -> None:
    entry = ConversationEntry(
        content="testing 123",
        role="assistant",
        timestamp=datetime.now(),
    )
    await memory_with_vector.add_conversation_entry("conv", entry, user_id="user")
    results = await memory_with_vector.conversation_search("testing", user_id="user")
    assert len(results) == 1
    assert results[0]["content"] == "testing 123"


@pytest.mark.asyncio
async def test_conversation_statistics(memory_with_vector: Memory) -> None:
    now = datetime.now()
    await memory_with_vector.add_conversation_entry(
        "c1",
        ConversationEntry(content="hi", role="user", timestamp=now),
        user_id="user",
    )
    await memory_with_vector.add_conversation_entry(
        "c1",
        ConversationEntry(
            content="bye", role="assistant", timestamp=now + timedelta(seconds=30)
        ),
        user_id="user",
    )
    await memory_with_vector.add_conversation_entry(
        "c2",
        ConversationEntry(
            content="ping", role="user", timestamp=now + timedelta(seconds=60)
        ),
        user_id="user",
    )
    stats = await memory_with_vector.conversation_statistics("user")
    assert stats["conversations"] == 2
    assert stats["messages"] == 3
    assert stats["average_length"] == 3
    assert stats["last_activity"] == (now + timedelta(seconds=60)).isoformat()
