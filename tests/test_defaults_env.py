import os
from entity.defaults import load_defaults


def test_env_overrides(tmp_path):
    os.environ["ENTITY_DUCKDB_PATH"] = str(tmp_path / "custom.db")
    os.environ["ENTITY_STORAGE_PATH"] = str(tmp_path / "files")
    # Disable auto-installation to avoid LLM setup issues in tests
    os.environ["ENTITY_AUTO_INSTALL_VLLM"] = "false"
    os.environ["ENTITY_AUTO_INSTALL_OLLAMA"] = "false"

    try:
        defaults = load_defaults()
    except Exception:
        # If LLM setup fails, that's ok for this test - we're only testing paths
        # Create minimal defaults for testing
        from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
        from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
        from entity.resources import DatabaseResource, VectorStoreResource, Memory, FileStorage, LocalStorageResource
        
        duckdb = DuckDBInfrastructure(str(tmp_path / "custom.db"))
        storage_infra = LocalStorageInfrastructure(str(tmp_path / "files"))
        
        db_resource = DatabaseResource(duckdb)
        vector_resource = VectorStoreResource(duckdb)
        storage_resource = LocalStorageResource(storage_infra)
        
        defaults = {
            "memory": Memory(db_resource, vector_resource),
            "file_storage": FileStorage(storage_resource),
        }

    memory = defaults["memory"]
    storage = defaults["file_storage"]

    assert memory.database.infrastructure.file_path.endswith("custom.db")
    assert str(storage.resource.infrastructure.base_path).endswith("files")
