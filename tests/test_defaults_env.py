from entity.defaults import load_defaults


def test_env_overrides(tmp_path):
    os.environ["ENTITY_DUCKDB_PATH"] = str(tmp_path / "custom.db")
    os.environ["ENTITY_STORAGE_PATH"] = str(tmp_path / "files")

    defaults = load_defaults()

    memory = defaults["memory"]
    storage = defaults["file_storage"]

    assert memory.database.infrastructure.file_path.endswith("custom.db")
    assert str(storage.resource.infrastructure.base_path).endswith("files")
