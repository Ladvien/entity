"""
Tests for the template plugin.
"""

from unittest.mock import Mock, patch

import pytest
from entity_plugin_template import TemplatePlugin


class TestTemplatePlugin:
    """Test cases for TemplatePlugin."""

    def test_init_with_default_config(self):
        """Test plugin initialization with default configuration."""
        plugin = TemplatePlugin()

        assert plugin.name == "template"
        assert plugin.version == "0.1.0"
        assert plugin.stage == "preprocessing"
        assert plugin.option1 == "default_value"
        assert plugin.option2 is False

    def test_init_with_custom_config(self):
        """Test plugin initialization with custom configuration."""
        config = {"stage": "processing", "option1": "custom_value", "option2": True}
        plugin = TemplatePlugin(config)

        assert plugin.stage == "processing"
        assert plugin.option1 == "custom_value"
        assert plugin.option2 is True

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = {"stage": "preprocessing"}
        plugin = TemplatePlugin(config)

        # Should not raise any exception
        plugin.validate_config()

    def test_validate_config_invalid_stage(self):
        """Test configuration validation with invalid stage."""
        config = {"stage": "invalid_stage"}

        with pytest.raises(ValueError, match="Stage must be one of"):
            TemplatePlugin(config)

    @pytest.mark.asyncio
    async def test_execute_basic_processing(self):
        """Test plugin execution with basic processing."""
        plugin = TemplatePlugin({"option2": False})

        # Mock workflow context
        context = Mock()
        context.get_data.return_value = {"input": "test_data"}
        context.set_data = Mock()
        context.add_metadata = Mock()

        result = await plugin.execute(context)

        # Verify context methods were called
        context.get_data.assert_called_once()
        context.set_data.assert_called_once()
        context.add_metadata.assert_called_once()

        # Verify the processed data
        call_args = context.set_data.call_args[0][0]
        assert call_args["input"] == "test_data"
        assert call_args["template_processed"] is True
        assert call_args["option1_value"] == "default_value"

        # Verify metadata
        metadata_args = context.add_metadata.call_args[0][0]
        assert metadata_args["plugin"] == "template"
        assert metadata_args["processed"] is True

        assert result == context

    @pytest.mark.asyncio
    async def test_execute_advanced_processing(self):
        """Test plugin execution with advanced processing."""
        plugin = TemplatePlugin({"option2": True})

        # Mock workflow context
        context = Mock()
        context.get_data.return_value = {"input": "test_data"}
        context.set_data = Mock()
        context.add_metadata = Mock()

        with patch.object(plugin, "_get_timestamp", return_value="2024-01-01T12:00:00"):
            result = await plugin.execute(context)

        # Verify the processed data includes advanced processing
        call_args = context.set_data.call_args[0][0]
        assert call_args["advanced_processing"] is True
        assert call_args["processing_timestamp"] == "2024-01-01T12:00:00"

        assert result == context

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """Test plugin execution when an error occurs."""
        plugin = TemplatePlugin()

        # Mock workflow context to raise an error
        context = Mock()
        context.get_data.side_effect = Exception("Test error")
        context.add_error = Mock()

        with pytest.raises(Exception, match="Test error"):
            await plugin.execute(context)

        context.add_error.assert_called_once()

    def test_basic_processing_dict(self):
        """Test basic processing with dictionary data."""
        plugin = TemplatePlugin({"option1": "test_value"})

        data = {"original": "data"}
        result = plugin._basic_processing(data)

        assert result["original"] == "data"
        assert result["template_processed"] is True
        assert result["option1_value"] == "test_value"

    def test_basic_processing_non_dict(self):
        """Test basic processing with non-dictionary data."""
        plugin = TemplatePlugin()

        data = "string_data"
        result = plugin._basic_processing(data)

        # Non-dict data should be returned unchanged
        assert result == "string_data"

    def test_advanced_processing(self):
        """Test advanced processing functionality."""
        plugin = TemplatePlugin()

        data = {"test": "data"}

        with patch.object(plugin, "_get_timestamp", return_value="2024-01-01T12:00:00"):
            result = plugin._advanced_processing(data)

        # Should include basic processing results
        assert result["template_processed"] is True

        # Should include advanced processing results
        assert result["advanced_processing"] is True
        assert result["processing_timestamp"] == "2024-01-01T12:00:00"

    def test_get_timestamp(self):
        """Test timestamp generation."""
        from unittest.mock import patch

        plugin = TemplatePlugin()

        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-01T12:00:00"
            )

            timestamp = plugin._get_timestamp()

            assert timestamp == "2024-01-01T12:00:00"
            mock_datetime.now.assert_called_once()

    def test_get_info(self):
        """Test plugin information retrieval."""
        config = {"stage": "processing", "option1": "test"}
        plugin = TemplatePlugin(config)

        info = plugin.get_info()

        assert info["name"] == "template"
        assert info["version"] == "0.1.0"
        assert info["stage"] == "processing"
        assert info["description"] == "Template plugin for Entity Framework"
        assert info["config"] == config
        assert "basic_processing" in info["capabilities"]
        assert "advanced_processing" in info["capabilities"]
        assert "metadata_addition" in info["capabilities"]

    def test_health_check_success(self):
        """Test successful health check."""
        plugin = TemplatePlugin()

        assert plugin.health_check() is True

    def test_health_check_invalid_config(self):
        """Test health check with invalid configuration."""
        plugin = TemplatePlugin()

        # Temporarily break the plugin
        plugin.name = None

        assert plugin.health_check() is False

    def test_health_check_validation_error(self):
        """Test health check when validation fails."""
        plugin = TemplatePlugin()

        # Mock validate_config to raise an exception
        with patch.object(
            plugin, "validate_config", side_effect=ValueError("Invalid config")
        ):
            assert plugin.health_check() is False


class TestTemplatePluginIntegration:
    """Integration tests for TemplatePlugin."""

    @pytest.mark.asyncio
    async def test_full_workflow_basic(self):
        """Test complete workflow with basic processing."""
        plugin = TemplatePlugin(
            {"stage": "preprocessing", "option1": "integration_test", "option2": False}
        )

        # Create mock context with realistic data
        context = Mock()
        input_data = {"text": "Hello world", "metadata": {"source": "test"}}
        context.get_data.return_value = input_data
        context.set_data = Mock()
        context.add_metadata = Mock()

        # Execute plugin
        result = await plugin.execute(context)

        # Verify processing
        processed_data = context.set_data.call_args[0][0]
        assert processed_data["text"] == "Hello world"
        assert processed_data["template_processed"] is True
        assert processed_data["option1_value"] == "integration_test"

        # Verify metadata
        metadata = context.add_metadata.call_args[0][0]
        assert metadata["plugin"] == "template"
        assert metadata["stage"] == "preprocessing"
        assert metadata["processed"] is True

        assert result == context

    @pytest.mark.asyncio
    async def test_full_workflow_advanced(self):
        """Test complete workflow with advanced processing."""
        plugin = TemplatePlugin(
            {"stage": "processing", "option1": "advanced_test", "option2": True}
        )

        # Create mock context
        context = Mock()
        input_data = {"data": "test_input"}
        context.get_data.return_value = input_data
        context.set_data = Mock()
        context.add_metadata = Mock()

        with patch.object(plugin, "_get_timestamp", return_value="2024-01-01T15:30:00"):
            # Execute plugin
            result = await plugin.execute(context)

        # Verify advanced processing was applied
        processed_data = context.set_data.call_args[0][0]
        assert processed_data["advanced_processing"] is True
        assert processed_data["processing_timestamp"] == "2024-01-01T15:30:00"

        assert result == context

    def test_plugin_info_consistency(self):
        """Test that plugin info is consistent with implementation."""
        plugin = TemplatePlugin()
        info = plugin.get_info()

        # Verify info matches plugin attributes
        assert info["name"] == plugin.name
        assert info["version"] == plugin.version
        assert info["stage"] == plugin.stage

        # Verify capabilities match available methods
        capabilities = info["capabilities"]
        assert "basic_processing" in capabilities
        assert "advanced_processing" in capabilities
        assert hasattr(plugin, "_basic_processing")
        assert hasattr(plugin, "_advanced_processing")


@pytest.fixture
def sample_plugin():
    """Fixture providing a sample plugin instance."""
    return TemplatePlugin(
        {"stage": "preprocessing", "option1": "fixture_value", "option2": False}
    )


@pytest.fixture
def sample_context():
    """Fixture providing a sample workflow context."""
    context = Mock()
    context.get_data.return_value = {"sample": "data", "number": 42}
    context.set_data = Mock()
    context.add_metadata = Mock()
    context.add_error = Mock()
    return context
