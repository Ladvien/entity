"""Tests for the request batching system."""

import asyncio
import time

import pytest

from entity.core.batch_executor import (
    BatchMetrics,
    BatchRequest,
    BatchWorkflowExecutor,
    Priority,
)
from entity.plugins.context import PluginContext
from entity.workflow.workflow import Workflow


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(self, name: str = "test_plugin", delay: float = 0.01):
        self.name = name
        self.delay = delay
        self.call_count = 0
        self.assigned_stage = "test"

    def should_execute(self, context: PluginContext) -> bool:
        return True

    async def execute(self, context: PluginContext) -> str:
        self.call_count += 1
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return f"{self.name}: {context.message}"


@pytest.fixture
def mock_resources():
    """Create mock resources for testing."""
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


@pytest.fixture
def mock_workflow():
    """Create a mock workflow for testing."""
    workflow = Workflow()
    workflow.steps = {
        "input": [MockPlugin("input_plugin", 0.01)],
        "parse": [MockPlugin("parse_plugin", 0.01)],
        "think": [MockPlugin("think_plugin", 0.02)],
        "do": [MockPlugin("do_plugin", 0.01)],
        "review": [MockPlugin("review_plugin", 0.01)],
        "output": [MockPlugin("output_plugin", 0.01)],
    }
    return workflow


class TestBatchRequest:
    """Test the BatchRequest data structure."""

    def test_batch_request_creation(self):
        """Test basic BatchRequest creation."""
        request = BatchRequest(
            message="test message",
            user_id="user123",
            priority=Priority.HIGH,
        )

        assert request.message == "test message"
        assert request.user_id == "user123"
        assert request.priority == Priority.HIGH
        assert isinstance(request.timestamp, float)
        assert isinstance(request.future, asyncio.Future)
        assert request.context_data == {}

    def test_batch_request_defaults(self):
        """Test BatchRequest with default values."""
        request = BatchRequest(
            message="test",
            user_id="user",
        )

        assert request.priority == Priority.NORMAL
        assert request.context_data == {}
        assert request.timestamp > 0


class TestBatchMetrics:
    """Test the BatchMetrics class."""

    def test_initial_metrics(self):
        """Test initial metrics state."""
        metrics = BatchMetrics()

        assert metrics.total_batches_processed == 0
        assert metrics.total_requests_processed == 0
        assert metrics.avg_batch_size == 0.0
        assert metrics.avg_batch_processing_time == 0.0
        assert metrics.avg_request_wait_time == 0.0
        assert metrics.timeouts == 0
        assert len(metrics.priority_distribution) == 0

    def test_update_batch_metrics(self):
        """Test batch metrics updates."""
        metrics = BatchMetrics()

        # Update with first batch
        metrics.update_batch_metrics(5, 1.0, [0.1, 0.2, 0.3, 0.4, 0.5])

        assert metrics.total_batches_processed == 1
        assert metrics.total_requests_processed == 5
        assert metrics.avg_batch_size == 5.0
        assert metrics.avg_batch_processing_time == 1.0
        assert metrics.avg_request_wait_time == 0.3  # (0.1+0.2+0.3+0.4+0.5)/5

        # Update with second batch
        metrics.update_batch_metrics(3, 0.5, [0.2, 0.3, 0.4])

        assert metrics.total_batches_processed == 2
        assert metrics.total_requests_processed == 8
        assert metrics.avg_batch_size == 4.0  # (5+3)/2
        assert metrics.avg_batch_processing_time == 0.75  # (1.0+0.5)/2
        # New weighted average: ((0.3*5) + (0.3*3)) / 8 = 0.3
        assert abs(metrics.avg_request_wait_time - 0.3) < 0.01


class TestBatchWorkflowExecutor:
    """Test the BatchWorkflowExecutor class."""

    @pytest.fixture
    async def batch_executor(self, mock_resources, mock_workflow):
        """Create a batch executor for testing."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=3,
            batch_timeout=0.05,
            adaptive_batching=False,  # Disable for predictable tests
        )
        yield executor
        await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_executor_initialization(self, mock_resources, mock_workflow):
        """Test batch executor initialization."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=10,
            batch_timeout=0.1,
            max_queue_size=100,
            adaptive_batching=True,
            priority_enabled=True,
        )

        assert executor.batch_size == 10
        assert executor.batch_timeout == 0.1
        assert executor.max_queue_size == 100
        assert executor.adaptive_batching is True
        assert executor.priority_enabled is True
        assert executor._processing_task is None

        await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_start_stop_batch_processing(self, batch_executor):
        """Test starting and stopping batch processing."""
        # Initially not started
        assert batch_executor._processing_task is None

        # Start processing
        await batch_executor.start_batch_processing()
        assert batch_executor._processing_task is not None
        assert not batch_executor._processing_task.done()

        # Stop processing
        await batch_executor.stop_batch_processing()
        assert (
            batch_executor._processing_task.done()
            or batch_executor._processing_task.cancelled()
        )

    @pytest.mark.asyncio
    async def test_single_request_execution(self, batch_executor):
        """Test processing a single request."""
        result = await batch_executor.execute_batch(
            message="Hello world",
            user_id="user123",
        )

        # Result should contain processed message from plugins
        assert isinstance(result, str)
        assert "Hello world" in result or result == "Hello world"

        # Check metrics
        metrics = batch_executor.get_batch_metrics()
        assert metrics["total_requests_processed"] >= 1

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, batch_executor):
        """Test processing multiple concurrent requests."""
        # Start multiple requests concurrently
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                batch_executor.execute_batch(
                    message=f"Message {i}",
                    user_id=f"user{i}",
                )
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, result in enumerate(results):
            assert isinstance(result, str)

        # Check metrics
        metrics = batch_executor.get_batch_metrics()
        assert metrics["total_requests_processed"] == 5
        assert metrics["total_batches_processed"] >= 1

    @pytest.mark.asyncio
    async def test_priority_queuing(self, mock_resources, mock_workflow):
        """Test priority-based request queuing."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=5,
            batch_timeout=0.1,
            priority_enabled=True,
        )

        try:
            # Submit requests with different priorities
            tasks = []

            # Low priority requests
            for i in range(2):
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"Low {i}",
                        user_id=f"low_user{i}",
                        priority=Priority.LOW,
                    )
                )
                tasks.append(task)

            # High priority requests
            for i in range(2):
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"High {i}",
                        user_id=f"high_user{i}",
                        priority=Priority.HIGH,
                    )
                )
                tasks.append(task)

            # Normal priority requests
            for i in range(2):
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"Normal {i}",
                        user_id=f"normal_user{i}",
                        priority=Priority.NORMAL,
                    )
                )
                tasks.append(task)

            # Wait for completion
            results = await asyncio.gather(*tasks)
            assert len(results) == 6

            # Check priority distribution in metrics
            metrics = executor.get_batch_metrics()
            priority_dist = metrics["priority_distribution"]
            assert priority_dist["LOW"] == 2
            assert priority_dist["NORMAL"] == 2
            assert priority_dist["HIGH"] == 2

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_batch_timeout(self, mock_resources, mock_workflow):
        """Test batch timeout functionality."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=10,  # Large batch size
            batch_timeout=0.05,  # Short timeout
        )

        try:
            # Submit fewer requests than batch size
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"Message {i}",
                        user_id=f"user{i}",
                    )
                )
                tasks.append(task)

            # Wait for completion - should timeout and process partial batch
            results = await asyncio.gather(*tasks)
            assert len(results) == 3

            # Should have processed despite not filling batch
            metrics = executor.get_batch_metrics()
            assert metrics["total_requests_processed"] == 3
            assert metrics["avg_batch_size"] < 10

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_request_timeout(self, batch_executor):
        """Test individual request timeout."""
        # Submit request with short timeout
        with pytest.raises(asyncio.TimeoutError):
            await batch_executor.execute_batch(
                message="test message",
                user_id="user123",
                timeout=0.001,  # Very short timeout
            )

        # Check that timeout was recorded in metrics
        metrics = batch_executor.get_batch_metrics()
        assert metrics["timeouts"] >= 1

    @pytest.mark.asyncio
    async def test_adaptive_batching(self, mock_resources, mock_workflow):
        """Test adaptive batching functionality."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=5,
            batch_timeout=0.1,
            adaptive_batching=True,
        )

        try:
            # Simulate high load to trigger batch size increase
            tasks = []
            for i in range(15):  # More than 2x batch size
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"Message {i}",
                        user_id=f"user{i}",
                    )
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            assert len(results) == 15

            metrics = executor.get_batch_metrics()
            assert metrics["total_requests_processed"] == 15

            # Adaptive batch size should be available in metrics
            assert "adaptive_batch_size" in metrics
            assert isinstance(metrics["adaptive_batch_size"], int)

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_metrics_collection(self, batch_executor):
        """Test comprehensive metrics collection."""
        # Process multiple batches
        for batch_num in range(3):
            tasks = []
            for i in range(2):
                task = asyncio.create_task(
                    batch_executor.execute_batch(
                        message=f"Batch {batch_num} Message {i}",
                        user_id=f"user{batch_num}_{i}",
                        priority=Priority.HIGH if i == 0 else Priority.NORMAL,
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Check final metrics
        metrics = batch_executor.get_batch_metrics()

        # Required fields
        required_fields = [
            "total_batches_processed",
            "total_requests_processed",
            "avg_batch_size",
            "avg_batch_processing_time",
            "avg_request_wait_time",
            "timeouts",
            "priority_distribution",
            "queue_size",
            "current_load",
        ]

        for field in required_fields:
            assert field in metrics, f"Missing metric field: {field}"

        assert metrics["total_requests_processed"] == 6
        assert metrics["priority_distribution"]["HIGH"] == 3
        assert metrics["priority_distribution"]["NORMAL"] == 3

    @pytest.mark.asyncio
    async def test_metrics_reset(self, batch_executor):
        """Test metrics reset functionality."""
        # Process some requests
        await batch_executor.execute_batch("test message", "user123")

        # Check metrics are populated
        metrics = batch_executor.get_batch_metrics()
        assert metrics["total_requests_processed"] > 0

        # Reset metrics
        batch_executor.reset_batch_metrics()

        # Check metrics are cleared
        metrics = batch_executor.get_batch_metrics()
        assert metrics["total_requests_processed"] == 0
        assert metrics["total_batches_processed"] == 0
        assert metrics["avg_batch_size"] == 0.0

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_resources, mock_workflow):
        """Test async context manager functionality."""
        async with BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
        ) as executor:
            result = await executor.execute_batch("test message", "user123")
            assert isinstance(result, str)

        # Executor should be stopped after context exit
        assert executor._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_queue_full_handling(self, mock_resources, mock_workflow):
        """Test handling of full request queue."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            max_queue_size=2,  # Small queue
            batch_size=1,
            batch_timeout=0.5,  # Long timeout to prevent processing
        )

        try:
            # Fill the queue
            task1 = asyncio.create_task(executor.execute_batch("message1", "user1"))
            task2 = asyncio.create_task(executor.execute_batch("message2", "user2"))

            # Wait a bit for queue to fill
            await asyncio.sleep(0.01)

            # This should raise QueueFull exception
            with pytest.raises(asyncio.QueueFull):
                await executor.execute_batch("message3", "user3", timeout=0.1)

            # Cancel the first tasks to prevent hanging
            task1.cancel()
            task2.cancel()

            try:
                await task1
            except asyncio.CancelledError:
                pass
            try:
                await task2
            except asyncio.CancelledError:
                pass

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_error_handling_in_batch(self, mock_resources):
        """Test error handling within batch processing."""

        # Create workflow with failing plugin
        class FailingPlugin:
            def __init__(self):
                self.assigned_stage = "think"

            def should_execute(self, context):
                return True

            async def execute(self, context):
                raise ValueError("Plugin execution failed")

        workflow = Workflow()
        workflow.steps = {
            "input": [MockPlugin("input_plugin")],
            "think": [FailingPlugin()],
            "output": [MockPlugin("output_plugin")],
        }

        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=workflow,
            batch_size=2,
        )

        try:
            # Submit requests that will fail
            with pytest.raises(ValueError, match="Plugin execution failed"):
                await executor.execute_batch("test message", "user123")

        finally:
            await executor.stop_batch_processing()


class TestPriority:
    """Test the Priority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.LOW.value == 1
        assert Priority.NORMAL.value == 2
        assert Priority.HIGH.value == 3
        assert Priority.CRITICAL.value == 4

    def test_priority_ordering(self):
        """Test priority ordering for queues."""
        priorities = [Priority.LOW, Priority.HIGH, Priority.NORMAL, Priority.CRITICAL]
        sorted_priorities = sorted(priorities, key=lambda p: p.value)

        expected_order = [
            Priority.LOW,
            Priority.NORMAL,
            Priority.HIGH,
            Priority.CRITICAL,
        ]
        assert sorted_priorities == expected_order


class TestIntegration:
    """Integration tests for the complete batch processing system."""

    @pytest.mark.asyncio
    async def test_high_throughput_scenario(self, mock_resources, mock_workflow):
        """Test high throughput batch processing scenario."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=20,
            batch_timeout=0.1,
            adaptive_batching=True,
            priority_enabled=True,
        )

        try:
            # Submit many concurrent requests
            num_requests = 100
            tasks = []

            for i in range(num_requests):
                priority = Priority.HIGH if i % 10 == 0 else Priority.NORMAL
                task = asyncio.create_task(
                    executor.execute_batch(
                        message=f"Request {i}",
                        user_id=f"user{i % 20}",  # 20 different users
                        priority=priority,
                    )
                )
                tasks.append(task)

            # Wait for all requests to complete
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            # Verify all requests completed
            assert len(results) == num_requests
            for result in results:
                assert isinstance(result, str)

            # Check performance metrics
            metrics = executor.get_batch_metrics()
            assert metrics["total_requests_processed"] == num_requests
            assert metrics["total_batches_processed"] >= 1

            # Calculate throughput
            throughput = num_requests / total_time
            print(f"Throughput: {throughput:.2f} requests/second")

            # Should achieve reasonable throughput (at least 50 req/sec)
            assert throughput > 50, f"Throughput too low: {throughput:.2f} req/sec"

        finally:
            await executor.stop_batch_processing()

    @pytest.mark.asyncio
    async def test_mixed_load_patterns(self, mock_resources, mock_workflow):
        """Test system behavior under varying load patterns."""
        executor = BatchWorkflowExecutor(
            resources=mock_resources,
            workflow=mock_workflow,
            batch_size=10,
            batch_timeout=0.05,
            adaptive_batching=True,
        )

        try:
            # Phase 1: Low load
            await asyncio.gather(
                *[executor.execute_batch(f"Low load {i}", f"user{i}") for i in range(3)]
            )

            # Phase 2: Burst load
            await asyncio.gather(
                *[executor.execute_batch(f"Burst {i}", f"user{i}") for i in range(25)]
            )

            # Phase 3: Sustained high load
            tasks = []
            for i in range(50):
                tasks.append(
                    asyncio.create_task(
                        executor.execute_batch(f"Sustained {i}", f"user{i}")
                    )
                )
                if i % 10 == 9:  # Add some delay every 10 requests
                    await asyncio.sleep(0.01)

            await asyncio.gather(*tasks)

            # Verify system handled all phases
            metrics = executor.get_batch_metrics()
            total_requests = 3 + 25 + 50  # 78 total
            assert metrics["total_requests_processed"] == total_requests

            # System should have adapted batch sizes
            if executor.adaptive_batching:
                assert metrics["adaptive_batch_size"] is not None

        finally:
            await executor.stop_batch_processing()
