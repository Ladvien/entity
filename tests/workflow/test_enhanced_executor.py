"""Tests for enhanced workflow executor with error context functionality."""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from entity.core.errors import PipelineError, PluginError, error_context_manager
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.resources import DatabaseResource, Memory, VectorStoreResource
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.workflow import Workflow


class TestErrorHandlingPlugin(Plugin):
    """Test plugin that can be configured to fail."""

    supported_stages = [
        "input",
        "think",
        "output",
        "error",
    ]  # Support all stages for testing

    def __init__(self, should_fail=False, failure_message="Test failure"):
        super().__init__(resources={}, config={})
        self.should_fail = should_fail
        self.failure_message = failure_message
        self.execution_count = 0

    async def _execute_impl(self, context: PluginContext) -> str:
        """Execute plugin, potentially failing."""
        self.execution_count += 1

        if self.should_fail:
            raise RuntimeError(self.failure_message)

        return f"TestPlugin executed {self.execution_count} times"


class TestEnhancedWorkflowExecutor:
    """Test enhanced WorkflowExecutor with error context."""

    @pytest.fixture
    def infrastructure(self):
        """Create test infrastructure."""
        return DuckDBInfrastructure(":memory:")

    @pytest.fixture
    def resources(self, infrastructure):
        """Create test resources."""
        return {
            "memory": Memory(
                DatabaseResource(infrastructure), VectorStoreResource(infrastructure)
            )
        }

    @pytest.fixture
    def workflow(self):
        """Create test workflow."""
        return Workflow()

    @pytest.fixture
    def executor(self, resources, workflow):
        """Create test executor."""
        return WorkflowExecutor(resources, workflow)

    @pytest.mark.asyncio
    async def test_execute_with_request_id_generation(self, executor):
        """Test that executor generates request ID automatically."""
        with patch.object(executor.workflow, "plugins_for", return_value=[]):
            result = await executor.execute("test message", "test_user")

            # Should complete without error
            assert result == "test message"

    @pytest.mark.asyncio
    async def test_execute_with_provided_request_id(self, executor):
        """Test executor with provided request ID."""
        request_id = str(uuid.uuid4())

        with patch.object(executor.workflow, "plugins_for", return_value=[]):
            result = await executor.execute("test message", "test_user", request_id)

            assert result == "test message"

    @pytest.mark.asyncio
    async def test_error_context_creation_and_cleanup(self, executor):
        """Test that error context is created and cleaned up properly."""
        request_id = str(uuid.uuid4())

        # Mock workflow to have no plugins
        with patch.object(executor.workflow, "plugins_for", return_value=[]):
            await executor.execute("test message", "test_user", request_id)

        # Context should be cleaned up after execution
        context = error_context_manager.get_context(request_id)
        assert context is None

    @pytest.mark.asyncio
    async def test_plugin_execution_with_error_tracking(self, executor):
        """Test plugin execution with error tracking."""
        # Create failing plugin
        failing_plugin = TestErrorHandlingPlugin(
            should_fail=True, failure_message="Plugin failed"
        )

        # Mock workflow to return failing plugin for INPUT stage
        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [failing_plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            # Execution should raise PluginError
            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user")

            # Check that error has enhanced context
            error = exc_info.value
            assert isinstance(error, PluginError)
            assert error.plugin == "TestErrorHandlingPlugin"
            assert error.stage == "input"
            assert str(error.original_error) == "Plugin failed"
            assert error.context.user_id == "test_user"

    @pytest.mark.asyncio
    async def test_plugin_stack_tracking(self, executor):
        """Test that plugin execution stack is tracked."""
        plugin1 = TestErrorHandlingPlugin(should_fail=False)
        plugin2 = TestErrorHandlingPlugin(should_fail=True)  # This will fail

        # Mock workflow to return plugins
        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [plugin1, plugin2]  # plugin2 will fail
                return []

            mock_plugins_for.side_effect = mock_plugins

            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user")

            # Check plugin stack is recorded
            error = exc_info.value
            assert "TestErrorHandlingPlugin" in error.context.plugin_stack

    @pytest.mark.asyncio
    async def test_execution_context_tracking(self, executor):
        """Test that execution context is tracked throughout pipeline."""
        plugin = TestErrorHandlingPlugin(should_fail=True)

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "think":  # Use think stage to test loop context
                    return [plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user")

            # Check execution context
            error = exc_info.value
            assert "loop_count" in error.context.execution_context
            assert "stage" in error.context.execution_context
            assert "current_plugin" in error.context.execution_context
            assert error.context.execution_context["stage"] == "think"

    @pytest.mark.asyncio
    async def test_error_recovery_plugins(self, executor):
        """Test error recovery through ERROR stage plugins."""
        failing_plugin = TestErrorHandlingPlugin(should_fail=True)
        recovery_plugin = Mock()
        recovery_plugin.execute = AsyncMock(return_value="Recovered")

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [failing_plugin]
                elif stage == "error":
                    return [recovery_plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            # Should still raise the original error but recovery plugin should run
            with pytest.raises(PluginError):
                await executor.execute("test message", "test_user")

            # Verify recovery plugin was called
            recovery_plugin.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_context_in_plugin_context(self, executor):
        """Test that error context is added to plugin context."""
        failing_plugin = TestErrorHandlingPlugin(should_fail=True)
        error_plugin = Mock()
        error_plugin.execute = AsyncMock()

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [failing_plugin]
                elif stage == "error":
                    return [error_plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            with pytest.raises(PluginError):
                await executor.execute("test message", "test_user")

            # Check that error plugin received enhanced context
            error_plugin.execute.assert_called_once()
            call_args = error_plugin.execute.call_args[0]
            plugin_context = call_args[0]

            assert hasattr(plugin_context, "error_context")
            assert plugin_context.error_context is not None
            assert "error_type" in plugin_context.error_context

    @pytest.mark.asyncio
    async def test_unhandled_exception_enhancement(self, executor):
        """Test enhancement of unhandled exceptions."""
        # Mock an exception that occurs outside plugin execution
        with patch.object(executor, "_run_stage") as mock_run_stage:
            mock_run_stage.side_effect = RuntimeError("Unhandled error")

            with pytest.raises(PipelineError) as exc_info:
                await executor.execute("test message", "test_user")

            # Check that exception was enhanced to PipelineError
            error = exc_info.value
            assert isinstance(error, PipelineError)
            assert str(error.original_error) == "Unhandled error"

    @pytest.mark.asyncio
    async def test_error_plugin_failure_handling(self, executor):
        """Test handling when error recovery plugins themselves fail."""
        failing_plugin = TestErrorHandlingPlugin(
            should_fail=True, failure_message="Original failure"
        )
        failing_error_plugin = Mock()
        failing_error_plugin.execute = AsyncMock(
            side_effect=RuntimeError("Error plugin failed")
        )
        failing_error_plugin.__class__.__name__ = "FailingErrorPlugin"

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [failing_plugin]
                elif stage == "error":
                    return [failing_error_plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            # Should still raise original error, not error plugin failure
            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user")

            # Original error should be preserved
            error = exc_info.value
            assert str(error.original_error) == "Original failure"

    def test_get_error_patterns(self, executor):
        """Test error pattern retrieval."""
        patterns = executor.get_error_patterns()
        assert isinstance(patterns, list)

    def test_get_debug_report(self, executor):
        """Test debug report generation."""
        request_id = str(uuid.uuid4())
        report = executor.get_debug_report(request_id)
        assert isinstance(report, str)
        assert request_id in report

    def test_analyze_recent_errors(self, executor):
        """Test recent error analysis."""
        analysis = executor.analyze_recent_errors(hours=1)
        assert isinstance(analysis, dict)
        assert "status" in analysis

    @pytest.mark.asyncio
    async def test_plugin_config_tracking(self, executor):
        """Test that plugin configuration is tracked in errors."""
        plugin = TestErrorHandlingPlugin(should_fail=True)
        plugin.config = {"setting1": "value1", "timeout": 30}

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:
            mock_plugins_for.side_effect = lambda stage: (
                [plugin] if stage == "input" else []
            )

            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user")

            error = exc_info.value
            assert hasattr(error, "plugin_config")
            assert error.plugin_config == {"setting1": "value1", "timeout": 30}

    @pytest.mark.asyncio
    async def test_request_id_propagation(self, executor):
        """Test that request ID is properly propagated through execution."""
        request_id = str(uuid.uuid4())
        plugin = TestErrorHandlingPlugin(should_fail=True)

        with patch.object(executor.workflow, "plugins_for") as mock_plugins_for:
            mock_plugins_for.side_effect = lambda stage: (
                [plugin] if stage == "input" else []
            )

            with pytest.raises(PluginError) as exc_info:
                await executor.execute("test message", "test_user", request_id)

            error = exc_info.value
            assert error.context.request_id == request_id


class TestErrorContextIntegration:
    """Integration tests for error context system."""

    @pytest.fixture
    def infrastructure(self):
        """Create test infrastructure."""
        return DuckDBInfrastructure(":memory:")

    @pytest.fixture
    def resources(self, infrastructure):
        """Create test resources."""
        return {
            "memory": Memory(
                DatabaseResource(infrastructure), VectorStoreResource(infrastructure)
            )
        }

    @pytest.mark.asyncio
    async def test_full_error_context_workflow(self, resources):
        """Test complete error context workflow with realistic scenario."""
        # Create workflow with multiple stages and plugins
        workflow = Workflow()
        executor = WorkflowExecutor(resources, workflow)

        # Create plugins for different stages
        input_plugin = TestErrorHandlingPlugin(should_fail=False)
        think_plugin = TestErrorHandlingPlugin(
            should_fail=True, failure_message="Analysis failed"
        )
        error_plugin = Mock()
        error_plugin.execute = AsyncMock(return_value="Error handled")

        with patch.object(workflow, "plugins_for") as mock_plugins_for:

            def mock_plugins(stage):
                if stage == "input":
                    return [input_plugin]
                elif stage == "think":
                    return [think_plugin]
                elif stage == "error":
                    return [error_plugin]
                return []

            mock_plugins_for.side_effect = mock_plugins

            request_id = str(uuid.uuid4())

            # Execute and expect failure
            with pytest.raises(PluginError) as exc_info:
                await executor.execute(
                    "Complex analysis task", "data_scientist", request_id
                )

            # Verify comprehensive error context
            error = exc_info.value

            # Basic error info
            assert error.context.request_id == request_id
            assert error.context.user_id == "data_scientist"
            assert error.stage == "think"
            assert error.plugin == "TestErrorHandlingPlugin"

            # Plugin stack should show execution path
            assert len(error.context.plugin_stack) >= 2  # input_plugin + think_plugin
            assert "TestErrorHandlingPlugin" in error.context.plugin_stack

            # Execution context should have stage info
            assert "stage" in error.context.execution_context
            assert "loop_count" in error.context.execution_context
            assert "current_plugin" in error.context.execution_context

            # Error should be properly categorized
            assert error.category is not None
            assert error.severity is not None

            # Error plugin should have been called
            error_plugin.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_analysis_integration(self, resources):
        """Test integration with error analysis system."""
        from entity.core.error_analysis import error_analyzer

        workflow = Workflow()
        executor = WorkflowExecutor(resources, workflow)

        failing_plugin = TestErrorHandlingPlugin(
            should_fail=True, failure_message="Network timeout"
        )

        with patch.object(workflow, "plugins_for") as mock_plugins_for:
            mock_plugins_for.side_effect = lambda stage: (
                [failing_plugin] if stage == "input" else []
            )

            # Execute multiple times to create pattern
            for i in range(3):
                with pytest.raises(PluginError):
                    await executor.execute(f"Request {i}", "test_user")

            # Check that error analyzer has recorded patterns
            patterns = error_analyzer.get_error_patterns(min_occurrences=2)
            assert len(patterns) > 0

            # Verify pattern contains our errors
            pattern = patterns[0]
            assert pattern.occurrences >= 3
            assert "input" in pattern.affected_stages
            assert "TestErrorHandlingPlugin" in pattern.affected_plugins
