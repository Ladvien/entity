import pytest
from datetime import datetime

from tests.conftest import AsyncPGDatabase
from entity.cli import EntityCLI
from entity.core.agent import Agent, _AgentRuntime
from entity.core.state import ConversationEntry
from entity.core.registries import PluginRegistry, SystemRegistries, ToolRegistry
from entity.core.resources.container import ResourceContainer
from entity.resources import Memory
from tests.resources.test_memory import DummyVector


@pytest.mark.asyncio
async def test_cli_get_conversation_stats(capsys, postgres_dsn: str) -> None:
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = DummyVector()
    await mem.initialize()
    await mem.add_conversation_entry(
        "c1",
        ConversationEntry(content="hi", role="user", timestamp=datetime.now()),
        user_id="user",
    )

    resources = ResourceContainer()
    await resources.add("memory", mem)
    runtime = _AgentRuntime(
        SystemRegistries(
            resources=resources, tools=ToolRegistry(), plugins=PluginRegistry()
        )
    )
    agent = Agent()
    agent._runtime = runtime

    cli = EntityCLI.__new__(EntityCLI)
    result = await cli._get_conversation_stats(agent, "user")
    captured = capsys.readouterr().out
    assert result == 0
    assert "conversations" in captured

    async with db.connection() as conn:
        await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
        await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")
