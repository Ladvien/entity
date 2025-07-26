import pytest
from entity.plugins.context import PluginContext
from entity.resources.logging import (
    LogCategory,
    LogLevel,
    RichConsoleLoggingResource,
)
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


@pytest.mark.asyncio
async def test_context_log_injects_ids() -> None:
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx = PluginContext(
        {"memory": memory, "logging": RichConsoleLoggingResource()}, user_id="u"
    )
    await ctx.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello")
    record = ctx.get_resource("logging").records[0]
    context_fields = record.get("context", {})
    assert context_fields["user_id"] == "u"
    assert record["category"] == LogCategory.USER_ACTION.value
