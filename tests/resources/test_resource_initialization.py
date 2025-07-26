import pytest

from entity.resources import (
    DatabaseResource,
    VectorStoreResource,
    LLMResource,
    LocalStorageResource,
    StorageResource,
    Memory,
    LLM,
    FileStorage,
    ResourceInitializationError,
)
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.resources.llm_protocol import LLMInfrastructure


class HealthyInfra:
    def health_check(self) -> bool:  # pragma: no cover - simple stub
        return True

    def __getattr__(self, name):  # pragma: no cover - stub
        def _noop(*args, **kwargs):
            return None

        return _noop


class FailingInfra:
    def health_check(self) -> bool:  # pragma: no cover - simple stub
        return False


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

    assert mem.health_check()
    assert llm.health_check()
    assert storage.health_check()


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
    with pytest.raises(ResourceInitializationError):
        Memory(DatabaseResource(FailingInfra()), None)
    with pytest.raises(ResourceInitializationError):
        LLM(None)
    with pytest.raises(ResourceInitializationError):
        FileStorage(None)


def test_infrastructures_satisfy_protocol():
    ollama = OllamaInfrastructure("http://localhost", "model", auto_install=False)
    vllm = VLLMInfrastructure("http://localhost:8000", "model")

    assert isinstance(ollama, LLMInfrastructure)
    assert isinstance(vllm, LLMInfrastructure)


def test_llm_resource_accepts_real_infrastructures():
    ollama = OllamaInfrastructure("http://localhost", "model", auto_install=False)
    vllm = VLLMInfrastructure("http://localhost:8000", "model")

    res_ollama = LLMResource(ollama)
    res_vllm = LLMResource(vllm)

    assert res_ollama.infrastructure is ollama
    assert res_vllm.infrastructure is vllm
