from unittest.mock import AsyncMock

from entity import _create_default_agent
from entity.utils.setup_manager import Layer0SetupManager
from entity.pipeline.stages import PipelineStage


def test_create_default_agent_brand_new_env(monkeypatch, tmp_path):
    def fake_init(
        self,
        db_path="./agent_memory.duckdb",
        files_dir="./agent_files",
        model="llama3",
        base_url="http://localhost:11434",
        logger=None,
        workflow=None,
    ):
        self.db_path = tmp_path / "memory.duckdb"
        self.files_dir = tmp_path / "files"
        self.model = model
        self.base_url = base_url
        self.logger = logger
        self.workflow = workflow

    async def fake_ensure(self):
        return True

    monkeypatch.setattr(Layer0SetupManager, "__init__", fake_init, raising=False)
    monkeypatch.setattr(Layer0SetupManager, "ensure_ollama", fake_ensure, raising=False)
    monkeypatch.setattr(Layer0SetupManager, "setup", AsyncMock())

    agent = _create_default_agent()
    resources = agent._runtime.capabilities.resources
    assert resources.get("vector_store") is not None
    assert resources.get("memory") is not None
    assert resources.get("database") is not None
    assert agent._runtime.workflow.stages.keys() == {
        PipelineStage.INPUT,
        PipelineStage.THINK,
        PipelineStage.OUTPUT,
        PipelineStage.ERROR,
    }
