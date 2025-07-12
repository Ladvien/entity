from contextlib import asynccontextmanager

from entity.resources import LLM, Memory, Storage, StandardResources
from entity.resources import memory as memory_module
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.storage import StorageResource


class DummyConnection:
    async def execute(
        self, query: str, params: tuple
    ) -> None:  # pragma: no cover - stub
        pass

    async def fetch(self, query: str, params: tuple) -> list:  # pragma: no cover - stub
        return []


class DummyDatabase(DatabaseResource):
    def __init__(self) -> None:
        super().__init__({})

    @asynccontextmanager
    async def connection(self):
        yield DummyConnection()


class DummyBackend(StorageResource):
    def __init__(self) -> None:
        super().__init__({})
        self._data: dict[str, str] = {}

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
    db = DummyDatabase()
    memory_module.database = db
    memory_module.vector_store = None
    memory = Memory(config={})

    res = StandardResources(
        memory=memory,
        llm=LLM(config={}),
        storage=Storage(backend=DummyBackend(), config={}),
    )
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
