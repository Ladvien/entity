import asyncio

import pytest

from entity.core.agent import Agent
from entity.config import load_config, clear_config_cache
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


def _memory() -> Memory:
    infra = DuckDBInfrastructure(":memory:")
    return Memory(DatabaseResource(infra), VectorStoreResource(infra))


@pytest.mark.asyncio
async def test_from_workflow(tmp_path):
    path = tmp_path / "wf.yaml"
    path.write_text(
        """\
think:
  - entity.plugins.defaults.ThinkPlugin
"""
    )
    agent = Agent.from_workflow(str(path), resources={"memory": _memory()})
    result = await agent.chat("hi")
    assert result["response"] == "hi"


@pytest.mark.asyncio
async def test_from_workflow_dict():
    agent = Agent.from_workflow_dict(
        {
            "think": ["entity.plugins.defaults.ThinkPlugin"],
        },
        resources={"memory": _memory()},
    )
    out = await agent.chat("hello")
    assert out["response"] == "hello"


def test_from_config(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        """\
resources: {}
workflow:
  think:
    - entity.plugins.defaults.ThinkPlugin
"""
    )
    agent = Agent.from_config(str(cfg), resources={"memory": _memory()})
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(agent.chat("hey"))
    assert result["response"] == "hey"


def test_config_cache(tmp_path):
    cfg = tmp_path / "conf.yml"
    cfg.write_text("resources: {}\nworkflow: {}")
    clear_config_cache()
    first = load_config(str(cfg))
    second = load_config(str(cfg))
    assert first is second
    clear_config_cache()
    third = load_config(str(cfg))
    assert first is not third
