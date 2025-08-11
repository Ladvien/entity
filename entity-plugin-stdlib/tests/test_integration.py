"""
Integration tests for the template plugin.
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from entity_plugin_template import TemplatePlugin


class TestTemplatePluginIntegration:
    """Integration tests that verify plugin works with Entity Framework interfaces."""

    def test_plugin_discovery(self):
        """Test that plugin can be discovered and loaded."""
        # Verify plugin can be imported and instantiated
        plugin = TemplatePlugin()

        assert plugin is not None
        assert hasattr(plugin, "execute")
        assert hasattr(plugin, "get_info")
        assert hasattr(plugin, "health_check")

    def test_plugin_registration(self):
        """Test plugin registration process."""
        plugin = TemplatePlugin(
            {"stage": "preprocessing", "option1": "registered_plugin"}
        )

        # Verify plugin can provide registration info
        info = plugin.get_info()

        assert info["name"] == "template"
        assert info["stage"] == "preprocessing"
        assert "capabilities" in info
        assert isinstance(info["capabilities"], list)

    @pytest.mark.asyncio
    async def test_workflow_integration(self):
        """Test integration with workflow execution."""
        # Create plugin
        plugin = TemplatePlugin(
            {"stage": "preprocessing", "option1": "workflow_test", "option2": False}
        )

        # Simulate workflow context
        context = Mock()
        workflow_data = {
            "id": "test_workflow_001",
            "input_text": "This is a test document for processing.",
            "metadata": {
                "source": "integration_test",
                "timestamp": "2024-01-01T10:00:00Z",
            },
        }
        context.get_data.return_value = workflow_data
        context.set_data = Mock()
        context.add_metadata = Mock()

        # Execute in workflow
        result_context = await plugin.execute(context)

        # Verify workflow integration
        assert result_context == context

        # Check that data was processed
        context.set_data.assert_called_once()
        processed_data = context.set_data.call_args[0][0]

        # Original data should be preserved
        assert processed_data["id"] == "test_workflow_001"
        assert processed_data["input_text"] == "This is a test document for processing."

        # Plugin processing should be applied
        assert processed_data["template_processed"] is True
        assert processed_data["option1_value"] == "workflow_test"

        # Metadata should be added
        context.add_metadata.assert_called_once()
        metadata = context.add_metadata.call_args[0][0]
        assert metadata["plugin"] == "template"
        assert metadata["stage"] == "preprocessing"
        assert metadata["processed"] is True

    @pytest.mark.asyncio
    async def test_pipeline_stage_execution(self):
        """Test plugin execution in different pipeline stages."""
        stages = ["preprocessing", "processing", "postprocessing"]

        for stage in stages:
            plugin = TemplatePlugin({"stage": stage, "option1": f"{stage}_test"})

            context = Mock()
            context.get_data.return_value = {"stage_test": True}
            context.set_data = Mock()
            context.add_metadata = Mock()

            await plugin.execute(context)

            # Verify stage-specific processing
            metadata = context.add_metadata.call_args[0][0]
            assert metadata["stage"] == stage

    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        # Test with invalid configuration
        with pytest.raises(ValueError):
            TemplatePlugin({"stage": "invalid"})

    @pytest.mark.asyncio
    async def test_context_error_propagation(self):
        """Test that plugin errors are properly added to context."""
        plugin = TemplatePlugin()

        context = Mock()
        context.get_data.side_effect = RuntimeError("Context data error")
        context.add_error = Mock()

        with pytest.raises(RuntimeError):
            await plugin.execute(context)

        # Verify error was added to context
        context.add_error.assert_called_once()
        error_call = context.add_error.call_args[0][0]
        assert "template: Context data error" in error_call

    def test_configuration_file_integration(self):
        """Test plugin configuration from file."""
        config_data = {
            "stage": "processing",
            "option1": "file_config_test",
            "option2": True,
        }

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            # Load config from file
            with open(config_file) as f:
                loaded_config = json.load(f)

            plugin = TemplatePlugin(loaded_config)

            # Verify configuration was loaded correctly
            assert plugin.stage == "processing"
            assert plugin.option1 == "file_config_test"
            assert plugin.option2 is True

        finally:
            os.unlink(config_file)

    @pytest.mark.asyncio
    async def test_multiple_plugin_instances(self):
        """Test multiple instances of the same plugin."""
        # Create multiple plugin instances with different configs
        plugin1 = TemplatePlugin({"stage": "preprocessing", "option1": "instance1"})
        plugin2 = TemplatePlugin(
            {"stage": "processing", "option1": "instance2", "option2": True}
        )

        # Create contexts for each
        context1 = Mock()
        context1.get_data.return_value = {"data": "test1"}
        context1.set_data = Mock()
        context1.add_metadata = Mock()

        context2 = Mock()
        context2.get_data.return_value = {"data": "test2"}
        context2.set_data = Mock()
        context2.add_metadata = Mock()

        # Execute both plugins
        await plugin1.execute(context1)
        await plugin2.execute(context2)

        # Verify each plugin processed independently
        data1 = context1.set_data.call_args[0][0]
        data2 = context2.set_data.call_args[0][0]

        assert data1["option1_value"] == "instance1"
        assert data2["option1_value"] == "instance2"
        assert "advanced_processing" not in data1
        assert data2.get("advanced_processing") is True

    def test_health_monitoring_integration(self):
        """Test plugin health monitoring capabilities."""
        plugin = TemplatePlugin()

        # Test healthy state
        assert plugin.health_check() is True

        # Test degraded state (simulate by corrupting internal state)
        original_name = plugin.name
        plugin.name = None

        assert plugin.health_check() is False

        # Restore and verify recovery
        plugin.name = original_name
        assert plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Test plugin behavior under concurrent execution."""
        import asyncio

        plugin = TemplatePlugin({"stage": "processing", "option1": "concurrent_test"})

        # Create multiple contexts
        contexts = []
        for i in range(5):
            context = Mock()
            context.get_data.return_value = {"batch": i, "data": f"test_{i}"}
            context.set_data = Mock()
            context.add_metadata = Mock()
            contexts.append(context)

        # Execute concurrently
        tasks = [plugin.execute(ctx) for ctx in contexts]
        results = await asyncio.gather(*tasks)

        # Verify all executions completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result == contexts[i]

            # Verify each context was processed
            contexts[i].set_data.assert_called_once()
            contexts[i].add_metadata.assert_called_once()

    def test_memory_usage_integration(self):
        """Test plugin memory behavior."""
        import gc

        # Create and destroy multiple plugin instances
        plugins = []
        for i in range(100):
            plugin = TemplatePlugin(
                {"stage": "preprocessing", "option1": f"memory_test_{i}"}
            )
            plugins.append(plugin)

        # Clear references
        plugins.clear()
        gc.collect()

        # Create new plugin to verify no memory leaks affected functionality
        test_plugin = TemplatePlugin()
        assert test_plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_data_serialization_integration(self):
        """Test plugin behavior with serializable data."""
        plugin = TemplatePlugin({"stage": "processing", "option2": True})

        # Test with JSON-serializable data
        context = Mock()
        serializable_data = {
            "text": "Test document",
            "numbers": [1, 2, 3, 4, 5],
            "nested": {"key": "value", "flag": True},
        }
        context.get_data.return_value = serializable_data
        context.set_data = Mock()
        context.add_metadata = Mock()

        with patch.object(plugin, "_get_timestamp", return_value="2024-01-01T12:00:00"):
            await plugin.execute(context)

        # Verify processed data is still serializable
        processed_data = context.set_data.call_args[0][0]

        # Should be JSON serializable
        import json

        json_str = json.dumps(processed_data)
        reloaded_data = json.loads(json_str)

        assert reloaded_data["text"] == "Test document"
        assert reloaded_data["template_processed"] is True
        assert reloaded_data["advanced_processing"] is True
