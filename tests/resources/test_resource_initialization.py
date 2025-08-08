import pytest

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.resources import (
    LLM,
    DatabaseResource,
    FileStorage,
    LLMResource,
    LocalStorageResource,
    Memory,
    ResourceInitializationError,
    StorageResource,
    VectorStoreResource,
)
from entity.resources.llm_protocol import LLMInfrastructure


class HealthyInfra:
    """Mock infrastructure that always returns healthy."""

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def health_check(self) -> bool:
        return True

    def health_check_sync(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        return "test response"


def test_constructors_success(tmp_path):
    duckdb = DuckDBInfrastructure(":memory:")
    db_res = DatabaseResource(duckdb)
    vector_res = VectorStoreResource(duckdb)
    mem = Memory(db_res, vector_res)

    llm_res = LLMResource(HealthyInfra())
    llm = LLM(llm_res)

    storage_infra = LocalStorageInfrastructure(tmp_path)
    local_res = LocalStorageResource(storage_infra)
    storage = FileStorage(local_res)

    assert mem.health_check_sync()
    assert llm.health_check_sync()
    assert storage.health_check_sync()


def test_constructor_failure():
    with pytest.raises(ResourceInitializationError):
        DatabaseResource(None)
    with pytest.raises(ResourceInitializationError):
        VectorStoreResource(None)
    with pytest.raises(ResourceInitializationError):
        LLMResource(None)
    with pytest.raises(ResourceInitializationError):
        LocalStorageResource(None)
    with pytest.raises(ResourceInitializationError):
        StorageResource(None)
    # Removed FailingInfra usage as per architecture compliance
    with pytest.raises(ResourceInitializationError):
        LLM(None)
    with pytest.raises(ResourceInitializationError):
        FileStorage(None)


def test_infrastructures_satisfy_protocol():
    ollama = OllamaInfrastructure("http://localhost", "model")

    assert isinstance(ollama, LLMInfrastructure)


def test_llm_resource_accepts_real_infrastructures():
    ollama = OllamaInfrastructure("http://localhost", "model")

    res_ollama = LLMResource(ollama)

    assert res_ollama.infrastructure is ollama
