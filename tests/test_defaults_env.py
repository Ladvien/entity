from entity.defaults import load_defaults


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_OLLAMA", "0")
    monkeypatch.setenv("ENTITY_AUTO_INSTALL_VLLM", "0")
    monkeypatch.setenv("ENTITY_DUCKDB_PATH", str(tmp_path / "custom.db"))
    monkeypatch.setenv("ENTITY_OLLAMA_URL", "http://example.com")
    monkeypatch.setenv("ENTITY_OLLAMA_MODEL", "dummy")
    monkeypatch.setenv("ENTITY_STORAGE_PATH", str(tmp_path / "files"))

    defaults = load_defaults()

    memory = defaults["memory"]
    llm = defaults["llm"]
    storage = defaults["file_storage"]

    assert memory.database.infrastructure.file_path.endswith("custom.db")
    llm_infra = llm.resource.infrastructure
    assert getattr(llm_infra, "base_url", "http://example.com") == "http://example.com"
    assert getattr(llm_infra, "model", "dummy") == "dummy"
    assert str(storage.resource.infrastructure.base_path).endswith("files")
