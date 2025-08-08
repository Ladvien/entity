import asyncio

import pytest

from entity.config import clear_config_cache, load_config
from entity.core.agent import Agent


@pytest.mark.asyncio
async def test_from_workflow(tmp_path):
    path = tmp_path / "wf.yaml"
    path.write_text(
        """\
think:
  - entity.plugins.defaults.ThinkPlugin
"""
    )
    agent = Agent.from_workflow(str(path))
    result = await agent.chat("hi")
    assert result == "hi"


@pytest.mark.asyncio
async def test_from_workflow_dict():
    agent = Agent.from_workflow_dict(
        {
            "think": ["entity.plugins.defaults.ThinkPlugin"],
        },
    )
    out = await agent.chat("hello")
    assert out == "hello"


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
    agent = Agent.from_config(str(cfg))
    result = asyncio.run(agent.chat("hey"))
    assert result == "hey"


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


@pytest.mark.integration
@pytest.mark.requires_ollama
def test_from_config_caching(tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        """
resources: {}
workflow:
  think:
    - entity.plugins.defaults.ThinkPlugin
"""
    )
    Agent.clear_from_config_cache()
    a1 = Agent.from_config(cfg)
    a2 = Agent.from_config(cfg)
    assert a1 is a2
    Agent.clear_from_config_cache()
    a3 = Agent.from_config(cfg)
    assert a1 is not a3


def test_invalid_workflow_dict():
    with pytest.raises(Exception):
        Agent.from_workflow_dict({"bad_stage": ["entity.plugins.defaults.ThinkPlugin"]})
