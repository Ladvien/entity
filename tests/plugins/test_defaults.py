"""Comprehensive tests for the consolidated default plugins."""

from unittest.mock import Mock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.defaults import (
    DoPlugin,
    InputPlugin,
    OutputPlugin,
    ParsePlugin,
    PassThroughPlugin,
    ReviewPlugin,
    ThinkPlugin,
    default_workflow,
)
from entity.workflow.executor import WorkflowExecutor


class TestPassThroughPlugin:
    """Test cases for the unified PassThroughPlugin."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {"test_resource": Mock()}

    @pytest.fixture
    def mock_context(self):
        """Create mock plugin context."""
        context = Mock(spec=PluginContext)
        context.message = "test message"
        context.say = Mock()
        return context

    def test_passthrough_plugin_initialization(self, mock_resources):
        """Test PassThroughPlugin initialization with valid stage."""
        config = {"stage": WorkflowExecutor.INPUT}
        plugin = PassThroughPlugin(mock_resources, config)

        assert plugin.supported_stages == [WorkflowExecutor.INPUT]
        assert plugin.config.stage == WorkflowExecutor.INPUT
        assert plugin.config.enable_output_say is True

    def test_passthrough_plugin_missing_stage_config(self, mock_resources):
        """Test PassThroughPlugin fails without stage configuration."""
        with pytest.raises(
            ValueError, match="PassThroughPlugin configuration validation failed"
        ):
            PassThroughPlugin(mock_resources, {})

    def test_passthrough_plugin_invalid_stage(self, mock_resources):
        """Test PassThroughPlugin fails with invalid stage."""
        config = {"stage": "INVALID_STAGE"}
        with pytest.raises(ValueError, match="Invalid stage 'INVALID_STAGE'"):
            PassThroughPlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_passthrough_plugin_basic_execution(
        self, mock_resources, mock_context
    ):
        """Test basic message passthrough for non-OUTPUT stages."""
        config = {"stage": WorkflowExecutor.INPUT}
        plugin = PassThroughPlugin(mock_resources, config)

        result = await plugin._execute_impl(mock_context)

        assert result == "test message"
        mock_context.say.assert_not_called()

    @pytest.mark.asyncio
    async def test_passthrough_plugin_output_stage_with_say(
        self, mock_resources, mock_context
    ):
        """Test OUTPUT stage calls context.say() when enabled."""
        config = {"stage": WorkflowExecutor.OUTPUT, "enable_output_say": True}
        plugin = PassThroughPlugin(mock_resources, config)

        result = await plugin._execute_impl(mock_context)

        assert result == "test message"
        mock_context.say.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_passthrough_plugin_output_stage_without_say(
        self, mock_resources, mock_context
    ):
        """Test OUTPUT stage skips context.say() when disabled."""
        config = {"stage": WorkflowExecutor.OUTPUT, "enable_output_say": False}
        plugin = PassThroughPlugin(mock_resources, config)

        result = await plugin._execute_impl(mock_context)

        assert result == "test message"
        mock_context.say.assert_not_called()

    @pytest.mark.asyncio
    async def test_passthrough_plugin_empty_message(self, mock_resources, mock_context):
        """Test handling of empty/None messages."""
        mock_context.message = None
        config = {"stage": WorkflowExecutor.PARSE}
        plugin = PassThroughPlugin(mock_resources, config)

        result = await plugin._execute_impl(mock_context)

        assert result == ""

    def test_passthrough_plugin_all_valid_stages(self, mock_resources):
        """Test PassThroughPlugin can be configured for all valid stages."""
        valid_stages = [
            WorkflowExecutor.INPUT,
            WorkflowExecutor.PARSE,
            WorkflowExecutor.THINK,
            WorkflowExecutor.DO,
            WorkflowExecutor.REVIEW,
            WorkflowExecutor.OUTPUT,
        ]

        for stage in valid_stages:
            config = {"stage": stage}
            plugin = PassThroughPlugin(mock_resources, config)
            assert plugin.supported_stages == [stage]
            assert plugin.config.stage == stage


class TestFactoryFunctions:
    """Test cases for backward compatibility factory functions."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {"test_resource": Mock()}

    def test_input_plugin_factory(self, mock_resources):
        """Test InputPlugin factory function."""
        plugin = InputPlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.INPUT]
        assert plugin.config.stage == WorkflowExecutor.INPUT

    def test_parse_plugin_factory(self, mock_resources):
        """Test ParsePlugin factory function."""
        plugin = ParsePlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.PARSE]
        assert plugin.config.stage == WorkflowExecutor.PARSE

    def test_think_plugin_factory(self, mock_resources):
        """Test ThinkPlugin factory function."""
        plugin = ThinkPlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.THINK]
        assert plugin.config.stage == WorkflowExecutor.THINK

    def test_do_plugin_factory(self, mock_resources):
        """Test DoPlugin factory function."""
        plugin = DoPlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.DO]
        assert plugin.config.stage == WorkflowExecutor.DO

    def test_review_plugin_factory(self, mock_resources):
        """Test ReviewPlugin factory function."""
        plugin = ReviewPlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.REVIEW]
        assert plugin.config.stage == WorkflowExecutor.REVIEW

    def test_output_plugin_factory(self, mock_resources):
        """Test OutputPlugin factory function."""
        plugin = OutputPlugin(mock_resources)
        assert isinstance(plugin, PassThroughPlugin)
        assert plugin.supported_stages == [WorkflowExecutor.OUTPUT]
        assert plugin.config.stage == WorkflowExecutor.OUTPUT
        assert plugin.config.enable_output_say is True

    def test_factory_functions_with_config(self, mock_resources):
        """Test factory functions accept additional configuration."""
        custom_config = {"enable_output_say": False}
        plugin = OutputPlugin(mock_resources, custom_config)
        assert plugin.config.enable_output_say is False
        assert plugin.config.stage == WorkflowExecutor.OUTPUT

    @pytest.mark.asyncio
    async def test_factory_function_behavior_matches_original(self, mock_resources):
        """Test that factory functions produce plugins with original behavior."""
        context = Mock(spec=PluginContext)
        context.message = "test message"
        context.say = Mock()

        # Test each factory function
        plugins = [
            InputPlugin(mock_resources),
            ParsePlugin(mock_resources),
            ThinkPlugin(mock_resources),
            DoPlugin(mock_resources),
            ReviewPlugin(mock_resources),
        ]

        # All non-OUTPUT plugins should just return the message
        for plugin in plugins:
            result = await plugin._execute_impl(context)
            assert result == "test message"
            context.say.assert_not_called()

        # OUTPUT plugin should call say()
        output_plugin = OutputPlugin(mock_resources)
        result = await output_plugin._execute_impl(context)
        assert result == "test message"
        context.say.assert_called_once_with("test message")


class TestDefaultWorkflow:
    """Test cases for the default_workflow function."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {"test_resource": Mock()}

    def test_default_workflow_creation(self, mock_resources):
        """Test default_workflow creates proper workflow structure."""
        workflow = default_workflow(mock_resources)

        # Check that all stages are present
        expected_stages = [
            WorkflowExecutor.INPUT,
            WorkflowExecutor.PARSE,
            WorkflowExecutor.THINK,
            WorkflowExecutor.DO,
            WorkflowExecutor.REVIEW,
            WorkflowExecutor.OUTPUT,
        ]

        for stage in expected_stages:
            assert stage in workflow.steps
            assert len(workflow.steps[stage]) == 1
            assert isinstance(workflow.steps[stage][0], PassThroughPlugin)

    def test_default_workflow_plugin_configuration(self, mock_resources):
        """Test that workflow plugins are configured for correct stages."""
        workflow = default_workflow(mock_resources)

        # Verify each plugin is configured for its assigned stage
        assert (
            workflow.steps[WorkflowExecutor.INPUT][0].config.stage
            == WorkflowExecutor.INPUT
        )
        assert (
            workflow.steps[WorkflowExecutor.PARSE][0].config.stage
            == WorkflowExecutor.PARSE
        )
        assert (
            workflow.steps[WorkflowExecutor.THINK][0].config.stage
            == WorkflowExecutor.THINK
        )
        assert (
            workflow.steps[WorkflowExecutor.DO][0].config.stage == WorkflowExecutor.DO
        )
        assert (
            workflow.steps[WorkflowExecutor.REVIEW][0].config.stage
            == WorkflowExecutor.REVIEW
        )
        assert (
            workflow.steps[WorkflowExecutor.OUTPUT][0].config.stage
            == WorkflowExecutor.OUTPUT
        )

        # Verify OUTPUT plugin has say enabled
        output_plugin = workflow.steps[WorkflowExecutor.OUTPUT][0]
        assert output_plugin.config.enable_output_say is True

    @pytest.mark.asyncio
    async def test_default_workflow_execution_compatibility(self, mock_resources):
        """Test that default workflow maintains backward compatibility."""
        workflow = default_workflow(mock_resources)

        context = Mock(spec=PluginContext)
        context.message = "test workflow message"
        context.say = Mock()

        # Test each stage plugin individually
        for stage, plugins in workflow.steps.items():
            plugin = plugins[0]  # Each stage has exactly one plugin
            result = await plugin._execute_impl(context)
            assert result == "test workflow message"

        # Verify OUTPUT stage called say()
        output_plugin = workflow.steps[WorkflowExecutor.OUTPUT][0]
        await output_plugin._execute_impl(context)
        context.say.assert_called_with("test workflow message")


class TestMemoryAndPerformanceImprovement:
    """Test cases focusing on memory usage and performance improvements."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {"test_resource": Mock()}

    def test_single_class_vs_multiple_classes(self, mock_resources):
        """Test that we now use a single class instead of 6 separate classes."""
        # Create plugins using factory functions (which all use PassThroughPlugin)
        input_plugin = InputPlugin(mock_resources)
        parse_plugin = ParsePlugin(mock_resources)
        think_plugin = ThinkPlugin(mock_resources)
        do_plugin = DoPlugin(mock_resources)
        review_plugin = ReviewPlugin(mock_resources)
        output_plugin = OutputPlugin(mock_resources)

        # All should be instances of the same class
        assert type(input_plugin) is type(parse_plugin) is type(think_plugin)
        assert type(do_plugin) is type(review_plugin) is type(output_plugin)
        assert all(
            isinstance(plugin, PassThroughPlugin)
            for plugin in [
                input_plugin,
                parse_plugin,
                think_plugin,
                do_plugin,
                review_plugin,
                output_plugin,
            ]
        )

    def test_reduced_code_duplication(self, mock_resources):
        """Test that plugins share the same implementation."""
        plugins = [
            InputPlugin(mock_resources),
            ParsePlugin(mock_resources),
            ThinkPlugin(mock_resources),
            DoPlugin(mock_resources),
            ReviewPlugin(mock_resources),
            OutputPlugin(mock_resources),
        ]

        # All plugins should have the same _execute_impl method
        execute_methods = [plugin._execute_impl for plugin in plugins]
        first_method = execute_methods[0]

        # All should reference the same method on the same class
        assert all(
            method.__func__ == first_method.__func__ for method in execute_methods
        )


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        return {"test_resource": Mock()}

    def test_passthrough_plugin_none_config(self, mock_resources):
        """Test PassThroughPlugin with None config."""
        with pytest.raises(
            ValueError, match="PassThroughPlugin configuration validation failed"
        ):
            PassThroughPlugin(mock_resources, None)

    def test_passthrough_plugin_empty_config(self, mock_resources):
        """Test PassThroughPlugin with empty config."""
        with pytest.raises(
            ValueError, match="PassThroughPlugin configuration validation failed"
        ):
            PassThroughPlugin(mock_resources, {})

    @pytest.mark.asyncio
    async def test_context_say_exception_handling(self, mock_resources):
        """Test that exceptions in context.say() propagate correctly."""
        mock_context = Mock(spec=PluginContext)
        mock_context.message = "test message"
        mock_context.say = Mock()
        mock_context.say.side_effect = Exception("Say failed")

        config = {"stage": WorkflowExecutor.OUTPUT}
        plugin = PassThroughPlugin(mock_resources, config)

        # Exception in say() should propagate
        with pytest.raises(Exception, match="Say failed"):
            await plugin._execute_impl(mock_context)

    def test_config_model_validation(self, mock_resources):
        """Test Pydantic config model validation."""
        # Valid config
        config = {"stage": WorkflowExecutor.INPUT, "enable_output_say": False}
        plugin = PassThroughPlugin(mock_resources, config)
        assert plugin.config.stage == WorkflowExecutor.INPUT
        assert plugin.config.enable_output_say is False

        # Invalid boolean value should be coerced
        config = {"stage": WorkflowExecutor.OUTPUT, "enable_output_say": "true"}
        plugin = PassThroughPlugin(mock_resources, config)
        assert plugin.config.enable_output_say is True


if __name__ == "__main__":
    pytest.main([__file__])
