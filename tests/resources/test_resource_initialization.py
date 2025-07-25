import pytest

from entity.resources import (
    DatabaseResource,
    VectorStoreResource,
    LLMResource,
    LocalStorageResource,
    StorageResource,
    Memory,
    LLM,
    Storage,
    ResourceInitializationError,
)
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure


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
    s3_res = StorageResource(HealthyInfra())
    storage = Storage(local_res)

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
        Storage(None)
