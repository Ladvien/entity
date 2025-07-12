from contextlib import asynccontextmanager
from entity.resources import LLM, Memory, Storage, StandardResources
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.vector_store import VectorStoreResource


class _DBConn:
    async def execute(self, *args):
        return None

    async def fetch(self, *args):
        return []


class DummyDB(DatabaseResource):
    @asynccontextmanager
    async def connection(self):
        yield _DBConn()


class DummyVector(VectorStoreResource):
    async def add_embedding(self, text: str) -> None:
        return None

    async def query_similar(self, query: str, k: int = 5) -> list[str]:
        return []


def test_standard_resources_types() -> None:
    res = StandardResources(
        memory=Memory(database=DummyDB(), vector_store=DummyVector(), config={}),
        llm=LLM(config={}),
        storage=Storage(backend=DummyBackend(), config={}),
    )
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
