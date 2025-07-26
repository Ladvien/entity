import pytest

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.infrastructure.s3_infra import S3Infrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure

from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.resources.llm import LLMResource
from entity.resources.storage import StorageResource
from entity.resources.local_storage import LocalStorageResource
from entity.resources.memory import Memory
from entity.resources.llm_wrapper import LLM
from entity.resources.file_storage_wrapper import FileStorage
from entity.resources.exceptions import ResourceInitializationError





def test_resources_store_injected_infrastructure(tmp_path):
    db_infra = DuckDBInfrastructure(str(tmp_path / "db.duckdb"))
    s3_infra = S3Infrastructure("bucket")
    ollama_infra = OllamaInfrastructure("http://localhost", "model")
    local_infra = LocalStorageInfrastructure(tmp_path)

    assert DatabaseResource(db_infra).infrastructure is db_infra
    assert VectorStoreResource(db_infra).infrastructure is db_infra
    assert LLMResource(ollama_infra).infrastructure is ollama_infra
    assert StorageResource(s3_infra).infrastructure is s3_infra
    assert LocalStorageResource(local_infra).infrastructure is local_infra


def test_wrappers_require_resources():
    with pytest.raises(ResourceInitializationError):
        Memory(None, None)
    with pytest.raises(ResourceInitializationError):
        LLM(None)
    with pytest.raises(ResourceInitializationError):
        FileStorage(None)
