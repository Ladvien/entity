from unittest.mock import AsyncMock

from entity import _create_default_agent
from entity.utils.setup_manager import Layer0SetupManager


def test_zero_config_initialization(monkeypatch, tmp_path):
    # avoid filesystem writes
    def fake_init(
        self,
        db_path="./agent_memory.duckdb",
        files_dir="./agent_files",
        model="llama3",
        base_url="http://localhost:11434",
        logger=None,
    ):
        self.db_path = tmp_path / "mem.duckdb"
        self.files_dir = tmp_path / "files"
        self.model = model
        self.base_url = base_url
        self.logger = logger

    monkeypatch.setattr(Layer0SetupManager, "__init__", fake_init, raising=False)
    monkeypatch.setattr(Layer0SetupManager, "setup", AsyncMock())

    agent = _create_default_agent()
    res = agent._runtime.capabilities.resources
    assert res.get("llm") is not None
    assert res.get("vector_store") is not None
    assert res.get("database") is not None
    assert res.get("memory") is not None
    assert res.get("logging") is not None
