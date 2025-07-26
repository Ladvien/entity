import pytest
from entity.plugins.context import PluginContext
from entity.resources.logging import (
    LogLevel,
    LogCategory,
    RichConsoleLoggingResource,
)
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


@pytest.mark.asyncio
async def test_context_log_injects_ids():
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx = PluginContext(
        {"memory": memory, "logging": RichConsoleLoggingResource()}, user_id="u"
    )
    await ctx.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello")
    record = ctx.get_resource("logging").records[0]
    fields = record["fields"]
    assert fields["user_id"] == "u"
    assert fields.get("workflow_id")
    assert fields.get("execution_id")
    assert fields["category"] == LogCategory.USER_ACTION.value
