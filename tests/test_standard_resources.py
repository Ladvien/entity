from entity.resources import LLM, Memory, Storage, StandardResources
from entity.resources.interfaces.storage import StorageResource


class DummyBackend(StorageResource):
    def __init__(self) -> None:
        super().__init__({})
        self._data: dict[str, str] = {}

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._data.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value


def test_standard_resources_types() -> None:
    res = StandardResources(
        memory=Memory(config={}),
        llm=LLM(config={}),
        storage=Storage(backend=DummyBackend(), config={}),
    )
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
