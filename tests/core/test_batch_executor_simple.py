"""Simple tests for the request batching system."""

import asyncio

import pytest

from entity.core.batch_executor import BatchWorkflowExecutor


@pytest.fixture
def simple_resources():
    """Create simple resources for testing."""
    from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
    from entity.resources import DatabaseResource, Memory, VectorStoreResource
    from entity.resources.logging import RichConsoleLoggingResource

    return {
        "memory": Memory(
            DatabaseResource(DuckDBInfrastructure(":memory:")),
            VectorStoreResource(DuckDBInfrastructure(":memory:")),
        ),
        "logging": RichConsoleLoggingResource(),
    }


class TestBasicBatchExecutor:
    """Test basic batch executor functionality."""

    @pytest.mark.asyncio
    async def test_basic_execution_without_workflow(self, simple_resources):
        """Test basic execution without complex workflow."""
        executor = BatchWorkflowExecutor(
            resources=simple_resources,
            workflow=None,  # Use default empty workflow
            batch_size=2,
            batch_timeout=0.1,
        )

        try:
            # Execute a simple request
            result = await asyncio.wait_for(
                executor.execute_batch("test message", "user123"),
                timeout=2.0,  # 2 second timeout
            )

            # Should return the message as-is since no plugins
            assert result == "test message"

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_executor_initialization(self, simple_resources):
        """Test executor initialization only."""
        executor = BatchWorkflowExecutor(
            resources=simple_resources,
            workflow=None,
            batch_size=5,
            batch_timeout=0.1,
        )

        assert executor.batch_size == 5
        assert executor.batch_timeout == 0.1
        assert executor._processing_task is None

        await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_metrics_basic(self, simple_resources):
        """Test basic metrics functionality."""
        executor = BatchWorkflowExecutor(
            resources=simple_resources,
            workflow=None,
            batch_size=1,
            batch_timeout=0.05,
        )

        try:
            # Get initial metrics
            metrics = executor.get_batch_metrics()
            assert metrics["total_requests_processed"] == 0

            # Process one request
            await asyncio.wait_for(executor.execute_batch("test", "user"), timeout=1.0)

            # Check metrics updated
            metrics = executor.get_batch_metrics()
            assert metrics["total_requests_processed"] == 1

        finally:
            await executor.stop_batch_processing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
