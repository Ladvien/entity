import logging
import pytest

from entity.pipeline.initializer import SystemInitializer
from entity.pipeline.stages import PipelineStage
from entity.core.plugins import PromptPlugin
from entity.resources.interfaces.database import DatabaseResource
from entity.resources.base import AgentResource as CanonicalResource  # noqa: F401
import entity.core.resources.container as container

container.CanonicalResource = CanonicalResource


class DummyDB(DatabaseResource):
    async def _execute_impl(self, context):
        pass


class MyPlugin(PromptPlugin):
    stage = PipelineStage.DO

    async def _execute_impl(self, context):
        pass


@pytest.mark.asyncio
async def test_stage_mismatch_warning(caplog):
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "database": {"type": __name__ + ":DummyDB"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            },
            "prompts": {"test": {"type": __name__ + ":MyPlugin", "stage": "think"}},
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg)
    with caplog.at_level(logging.WARNING):
        await init.initialize()
    assert any("override class stages" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_stage_mismatch_strict():
    cfg = {
        "plugins": {
            "agent_resources": {
                "memory": {"type": "entity.resources.memory:Memory"},
                "database": {"type": __name__ + ":DummyDB"},
                "llm": {"type": "entity.resources.llm:LLM"},
                "storage": {"type": "entity.resources.storage:Storage"},
            },
            "prompts": {"test": {"type": __name__ + ":MyPlugin", "stage": "think"}},
        },
        "workflow": {},
    }
    init = SystemInitializer(cfg, strict_stages=True)
    with pytest.raises(Exception):
        await init.initialize()
