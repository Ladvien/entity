"""Tests for enhanced error context and debugging utilities."""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from entity.core.errors import (
    ErrorCategory,
    ErrorContext,
    ErrorContextManager,
    ErrorSeverity,
    PipelineError,
    PluginError,
    ResourceError,
    SandboxError,
    ValidationError,
    error_context_manager,
)


class TestErrorContext:
    """Test ErrorContext dataclass."""

    def test_error_context_creation(self):
        """Test ErrorContext initialization."""
        request_id = str(uuid.uuid4())
        context = ErrorContext(
            request_id=request_id,
            user_id="test_user",
            timestamp=datetime.now(),
            stage="test_stage",
            plugin="test_plugin",
        )

        assert context.request_id == request_id
        assert context.user_id == "test_user"
        assert context.stage == "test_stage"
        assert context.plugin == "test_plugin"
        assert context.plugin_stack == []
        assert context.execution_context == {}
        assert context.recovery_attempted is False


class TestPipelineError:
    """Test PipelineError and related error types."""

    @pytest.fixture
    def sample_context(self):
        """Create sample error context."""
        return ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=datetime.now(),
            stage="test_stage",
            plugin="test_plugin",
            plugin_stack=["plugin1", "plugin2"],
            execution_context={"key": "value"},
        )

    def test_pipeline_error_creation(self, sample_context):
        """Test PipelineError creation."""
        original_error = ValueError("Test error")

        error = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=sample_context,
            original_error=original_error,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PLUGIN,
        )

        assert error.stage == "test_stage"
        assert error.plugin == "test_plugin"
        assert error.context == sample_context
        assert error.original_error == original_error
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.PLUGIN
        assert error.recoverable is True  # default

    def test_pipeline_error_string_representation(self, sample_context):
        """Test PipelineError string formatting."""
        original_error = ValueError("Test error")

        error = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=sample_context,
            original_error=original_error,
        )

        error_str = str(error)

        assert "Pipeline Error: ValueError" in error_str
        assert "Stage: test_stage" in error_str
        assert "Plugin: test_plugin" in error_str
        assert sample_context.request_id in error_str
        assert "Plugin Stack: plugin1 -> plugin2" in error_str
        assert "Original Error: Test error" in error_str

    def test_pipeline_error_to_dict(self, sample_context):
        """Test PipelineError serialization."""
        original_error = ValueError("Test error")

        error = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=sample_context,
            original_error=original_error,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PLUGIN,
        )

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "PipelineError"
        assert error_dict["stage"] == "test_stage"
        assert error_dict["plugin"] == "test_plugin"
        assert error_dict["request_id"] == sample_context.request_id
        assert error_dict["severity"] == "high"
        assert error_dict["category"] == "plugin"
        assert error_dict["original_error"]["type"] == "ValueError"
        assert error_dict["original_error"]["message"] == "Test error"


class TestSpecificErrorTypes:
    """Test specific error type implementations."""

    @pytest.fixture
    def sample_context(self):
        """Create sample error context."""
        return ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=datetime.now(),
            stage="test_stage",
        )

    def test_plugin_error(self, sample_context):
        """Test PluginError creation."""
        original_error = RuntimeError("Plugin failed")
        plugin_config = {"setting": "value"}

        error = PluginError(
            plugin_name="TestPlugin",
            stage="test_stage",
            context=sample_context,
            original_error=original_error,
            plugin_config=plugin_config,
        )

        assert error.plugin == "TestPlugin"
        assert error.stage == "test_stage"
        assert error.category == ErrorCategory.PLUGIN
        assert error.plugin_config == plugin_config

    def test_validation_error(self, sample_context):
        """Test ValidationError creation."""
        original_error = ValueError("Invalid input")
        field_errors = {"field1": ["required"], "field2": ["invalid format"]}

        error = ValidationError(
            field_errors=field_errors,
            context=sample_context,
            original_error=original_error,
        )

        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.field_errors == field_errors

    def test_resource_error(self, sample_context):
        """Test ResourceError creation."""
        original_error = ConnectionError("Database unavailable")

        error = ResourceError(
            resource_type="database",
            resource_id="main_db",
            context=sample_context,
            original_error=original_error,
        )

        assert error.category == ErrorCategory.RESOURCE
        assert error.severity == ErrorSeverity.HIGH
        assert error.resource_type == "database"
        assert error.resource_id == "main_db"

    def test_sandbox_error_security_violation(self, sample_context):
        """Test SandboxError with security violation."""
        original_error = SecurityError("Attempted file access")

        error = SandboxError(
            sandbox_type="docker",
            context=sample_context,
            original_error=original_error,
            security_violation=True,
        )

        assert error.category == ErrorCategory.SANDBOX
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recoverable is False
        assert error.security_violation is True


class TestErrorContextManager:
    """Test ErrorContextManager functionality."""

    @pytest.fixture
    def context_manager(self):
        """Create fresh ErrorContextManager for testing."""
        return ErrorContextManager()

    def test_create_context(self, context_manager):
        """Test context creation."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage", plugin="test_plugin"
        )

        assert context.user_id == "test_user"
        assert context.stage == "test_stage"
        assert context.plugin == "test_plugin"
        assert context.request_id in context_manager._active_contexts

    def test_get_context(self, context_manager):
        """Test context retrieval."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage"
        )

        retrieved = context_manager.get_context(context.request_id)
        assert retrieved == context

        # Test non-existent context
        assert context_manager.get_context("nonexistent") is None

    def test_update_plugin_stack(self, context_manager):
        """Test plugin stack tracking."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage"
        )

        context_manager.update_plugin_stack(context.request_id, "plugin1")
        context_manager.update_plugin_stack(context.request_id, "plugin2")

        assert context.plugin_stack == ["plugin1", "plugin2"]

    def test_add_execution_context(self, context_manager):
        """Test execution context addition."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage"
        )

        context_manager.add_execution_context(context.request_id, "key1", "value1")
        context_manager.add_execution_context(context.request_id, "key2", 42)

        assert context.execution_context == {"key1": "value1", "key2": 42}

    def test_classify_error(self, context_manager):
        """Test error classification."""
        # Test validation error
        validation_error = ValueError("Invalid input format")
        assert (
            context_manager.classify_error(validation_error) == ErrorCategory.VALIDATION
        )

        # Test network error
        network_error = ConnectionError("Connection timeout")
        assert context_manager.classify_error(network_error) == ErrorCategory.NETWORK

        # Test timeout error
        timeout_error = TimeoutError("Operation timed out")
        assert context_manager.classify_error(timeout_error) == ErrorCategory.TIMEOUT

        # Test unknown error
        unknown_error = RuntimeError("Unknown issue")
        assert context_manager.classify_error(unknown_error) == ErrorCategory.UNKNOWN

    def test_get_recovery_strategies(self, context_manager):
        """Test recovery strategy retrieval."""
        strategies = context_manager.get_recovery_strategies(ErrorCategory.NETWORK)
        assert len(strategies) > 0

        strategies = context_manager.get_recovery_strategies(ErrorCategory.UNKNOWN)
        assert strategies == []

    def test_create_pipeline_error(self, context_manager):
        """Test pipeline error creation with classification."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage"
        )
        original_error = ConnectionError("Network error")

        pipeline_error = context_manager.create_pipeline_error(
            stage="test_stage",
            plugin="test_plugin",
            original_error=original_error,
            context=context,
        )

        assert isinstance(pipeline_error, PipelineError)
        assert pipeline_error.category == ErrorCategory.NETWORK
        assert pipeline_error.original_error == original_error

    def test_error_pattern_recording(self, context_manager):
        """Test error pattern recording."""
        # Create similar errors
        context1 = context_manager.create_context("user1", "stage1")
        context2 = context_manager.create_context("user2", "stage1")

        error1 = ConnectionError("Connection failed")
        error2 = ConnectionError("Connection timeout")

        # Record errors
        _ = context_manager.create_pipeline_error("stage1", "plugin1", error1, context1)
        _ = context_manager.create_pipeline_error("stage1", "plugin1", error2, context2)

        # Check patterns are recorded
        patterns = context_manager.get_error_patterns()
        assert len(patterns) > 0

    def test_cleanup_context(self, context_manager):
        """Test context cleanup."""
        context = context_manager.create_context(
            user_id="test_user", stage="test_stage"
        )
        request_id = context.request_id

        assert request_id in context_manager._active_contexts

        context_manager.cleanup_context(request_id)
        assert request_id not in context_manager._active_contexts


class TestGlobalErrorContextManager:
    """Test global error context manager instance."""

    def test_global_instance_exists(self):
        """Test that global instance is available."""
        assert error_context_manager is not None
        assert isinstance(error_context_manager, ErrorContextManager)

    def test_global_instance_functionality(self):
        """Test basic functionality of global instance."""
        context = error_context_manager.create_context(
            user_id="global_test", stage="global_stage"
        )

        assert context.user_id == "global_test"
        assert context.stage == "global_stage"

        # Clean up
        error_context_manager.cleanup_context(context.request_id)


class TestErrorIntegration:
    """Test error system integration scenarios."""

    def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        # Create context
        context = error_context_manager.create_context(
            user_id="workflow_test", stage="test_stage", plugin="test_plugin"
        )

        # Add execution context
        error_context_manager.add_execution_context(
            context.request_id, "operation", "test_operation"
        )
        error_context_manager.update_plugin_stack(context.request_id, "plugin1")
        error_context_manager.update_plugin_stack(context.request_id, "plugin2")

        # Create error
        original_error = ValueError("Test workflow error")
        pipeline_error = error_context_manager.create_pipeline_error(
            stage="test_stage",
            plugin="test_plugin",
            original_error=original_error,
            context=context,
        )

        # Verify error has all context
        assert pipeline_error.context.plugin_stack == ["plugin1", "plugin2"]
        assert "operation" in pipeline_error.context.execution_context
        assert pipeline_error.context.execution_context["operation"] == "test_operation"

        # Test serialization
        error_dict = pipeline_error.to_dict()
        assert "plugin_stack" in error_dict
        assert "execution_context" in error_dict

        # Clean up
        error_context_manager.cleanup_context(context.request_id)

    @patch("entity.core.errors.datetime")
    def test_error_timing(self, mock_datetime):
        """Test error timing and context preservation."""
        # Mock consistent datetime
        fixed_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time

        context = error_context_manager.create_context(
            user_id="timing_test", stage="timing_stage"
        )

        assert context.timestamp == fixed_time

        # Clean up
        error_context_manager.cleanup_context(context.request_id)


# Custom exception for testing
class SecurityError(Exception):
    """Test security exception."""

    pass
