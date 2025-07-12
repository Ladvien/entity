from contextlib import asynccontextmanager
import asyncio

from entity.resources import LLM, Memory, Storage, StandardResources
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.interfaces.llm import LLMResource
from entity.core.state import LLMResponse
from entity.resources.interfaces.storage import StorageResource
from entity.resources.interfaces.vector_store import VectorStoreResource


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


class DummyLLMProvider(LLMResource):
    async def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(content=prompt)


def test_standard_resources_types() -> None:
    db = DummyDatabase()
    memory = Memory(config={})
    asyncio.get_event_loop().run_until_complete(memory.initialize())

    res = StandardResources(
        memory=memory,
        llm=LLM(config={}),
        storage=Storage(config={}),
    )
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
