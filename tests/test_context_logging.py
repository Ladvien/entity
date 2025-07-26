import pytest
from entity.plugins.context import PluginContext
from entity.resources.logging import (
    LogCategory,
    LogLevel,
    RichLoggingResource,
)
from entity.workflow.executor import WorkflowExecutor
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure

pytest.skip("Context logging integration unstable", allow_module_level=True)


@pytest.mark.asyncio
async def test_context_log_injects_ids() -> None:
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx = PluginContext(
        {"memory": memory, "logging": RichLoggingResource()}, user_id="u"
    )
    await ctx.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello")
    record = ctx.get_resource("logging").records[0]
    context = record["context"]
    assert context["user_id"] == "u"
    assert context.get("stage") == ctx.current_stage
    assert context.get("plugin_name") is None
    assert record["category"] == LogCategory.USER_ACTION.value
    assert record.get("fields") is not None
