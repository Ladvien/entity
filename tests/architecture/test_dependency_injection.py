import pytest
from datetime import datetime

from tests.conftest import AsyncPGDatabase
from entity.core.plugins import ValidationResult, ResourcePlugin
from entity.resources.base import AgentResource
from entity.resources import Memory
from entity.core.state import ConversationEntry


class DBInterface(ResourcePlugin):
    infrastructure_dependencies = ["database"]
    stages: list = []
    dependencies: list = []

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.database = None


class DepResource(AgentResource):
    dependencies = ["db"]
    stages: list = []

    def __init__(self, config=None) -> None:
        super().__init__(config or {})
        self.db = None

    @classmethod
    async def validate_dependencies(cls, registry):
        return ValidationResult.error_result("bad dependency")


DBInterface.dependencies = []
DepResource.dependencies = ["db"]


@pytest.mark.asyncio
async def test_memory_user_isolation(postgres_dsn: str) -> None:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()

    try:
        entry1 = ConversationEntry(content="one", role="user", timestamp=datetime.now())
        entry2 = ConversationEntry(content="two", role="user", timestamp=datetime.now())
        await mem.save_conversation("pipe", [entry1], user_id="u1")
        await mem.save_conversation("pipe", [entry2], user_id="u2")

        hist1 = await mem.load_conversation("pipe", user_id="u1")
        hist2 = await mem.load_conversation("pipe", user_id="u2")

        assert [e.content for e in hist1] == ["one"]
        assert [e.content for e in hist2] == ["two"]
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")
