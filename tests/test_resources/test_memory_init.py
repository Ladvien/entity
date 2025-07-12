import pytest
from entity.resources import Memory
from entity.resources.interfaces.vector_store import VectorStoreResource
from entity.resources.interfaces.database import DatabaseResource
from pipeline.errors import ResourceInitializationError
from contextlib import asynccontextmanager


class DummyDB(DatabaseResource):
    def get_connection_pool(self):
        class _Pool:
            def execute(self, *args, **kwargs):
                pass

        return _Pool()

    @asynccontextmanager
    async def connection(self):
        yield self.get_connection_pool()


class DummyVector(VectorStoreResource):
    async def add_embedding(self, text: str) -> None:
        return None

    async def query_similar(self, query: str, k: int = 5):
        return []


@pytest.mark.asyncio
async def test_initialize_without_database_raises():
    mem = Memory(config={})
    mem.vector_store = DummyVector()

    with pytest.raises(ResourceInitializationError, match="Database dependency"):
        await mem.initialize()


@pytest.mark.asyncio
async def test_initialize_without_vector_store_raises():
    mem = Memory(config={})
    mem.database = DummyDB()

    with pytest.raises(ResourceInitializationError, match="VectorStore dependency"):
        await mem.initialize()
