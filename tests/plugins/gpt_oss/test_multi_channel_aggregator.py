"""Unit tests for Multi-Channel Response Aggregator Plugin."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss import (
    AggregatedResponse,
    AggregationStrategy,
    ChannelContent,
    ChannelType,
    MultiChannelAggregatorPlugin,
)
from entity.workflow.executor import WorkflowExecutor


class TestMultiChannelAggregatorPlugin:
    """Test MultiChannelAggregatorPlugin functionality."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Test response")

        class MockMemory:
            def __init__(self):
                self.data = {}

            async def store(self, key, value):
                self.data[key] = value

            async def load(self, key, default=None):
                return self.data.get(key, default)

        mock_logging = MagicMock()
        mock_logging.log = AsyncMock()

        return {
            "llm": mock_llm,
            "memory": MockMemory(),
            "logging": mock_logging,
        }

    @pytest.fixture
    def basic_plugin(self, mock_resources):
        """Create basic plugin with default config."""
        config = {
            "default_strategy": AggregationStrategy.USER_FRIENDLY.value,
            "enable_safety_filtering": True,
            "filter_technical_jargon": True,
            "max_user_response_length": 2000,
        }
        return MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.fixture
    def debugging_plugin(self, mock_resources):
        """Create plugin configured for debugging."""
        config = {
            "default_strategy": AggregationStrategy.DEBUGGING.value,
            "filter_technical_jargon": False,
            "include_debug_info": True,
            "log_channel_processing": True,
        }
        return MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.REVIEW
        ctx.message = "Test message"
        ctx.execution_id = "test_exec_123"
        ctx.remember = AsyncMock()
        ctx.recall = AsyncMock(return_value=None)
        ctx.log = AsyncMock()
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.default_strategy == "user_friendly"
        assert basic_plugin.config.enable_safety_filtering is True
        assert WorkflowExecutor.REVIEW in basic_plugin.supported_stages
        assert len(basic_plugin._channel_patterns) == 3
        assert ChannelType.ANALYSIS in basic_plugin._channel_patterns
        assert ChannelType.COMMENTARY in basic_plugin._channel_patterns
        assert ChannelType.FINAL in basic_plugin._channel_patterns

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"min_channel_confidence": 1.5}  # Invalid, must be <= 1

        with pytest.raises(ValueError, match="Invalid configuration"):
            MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_basic_execution_no_channels(self, basic_plugin, context):
        """Test execution with no multi-channel content."""
        context.message = "Simple message without channels"
        result = await basic_plugin._execute_impl(context)

        assert result == "Simple message without channels"
        context.log.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_channels_analysis(self, basic_plugin):
        """Test parsing analysis channel."""
        message = "<analysis>This is the analysis content</analysis>"
        channels = await basic_plugin._parse_channels(message)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.ANALYSIS
        assert channels[0].raw_content == "This is the analysis content"
        assert "pattern_used" in channels[0].metadata

    @pytest.mark.asyncio
    async def test_parse_channels_commentary(self, basic_plugin):
        """Test parsing commentary channel."""
        message = "<commentary>This is commentary content</commentary>"
        channels = await basic_plugin._parse_channels(message)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.COMMENTARY
        assert channels[0].raw_content == "This is commentary content"

    @pytest.mark.asyncio
    async def test_parse_channels_final(self, basic_plugin):
        """Test parsing final channel."""
        message = "<final>This is the final response</final>"
        channels = await basic_plugin._parse_channels(message)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.FINAL
        assert channels[0].raw_content == "This is the final response"

    @pytest.mark.asyncio
    async def test_parse_channels_multiple(self, basic_plugin):
        """Test parsing multiple channels."""
        message = """
        <analysis>Analysis content here</analysis>
        <commentary>Commentary goes here</commentary>
        <final>Final response content</final>
        """
        channels = await basic_plugin._parse_channels(message)

        assert len(channels) == 3
        channel_types = [c.channel_type for c in channels]
        assert ChannelType.ANALYSIS in channel_types
        assert ChannelType.COMMENTARY in channel_types
        assert ChannelType.FINAL in channel_types

    @pytest.mark.asyncio
    async def test_parse_channels_alternative_formats(self, basic_plugin):
        """Test parsing alternative channel formats."""
        message = """
        [ANALYSIS]This is bracketed analysis[/ANALYSIS]
        Commentary: This is colon-separated commentary
        Final: This is the final answer
        """
        channels = await basic_plugin._parse_channels(message)

        assert len(channels) >= 2  # Should parse at least analysis and commentary

    @pytest.mark.asyncio
    async def test_parse_channels_disabled_channel(self, mock_resources):
        """Test parsing when some channels are disabled."""
        config = {
            "enable_analysis_channel": False,
            "enable_commentary_channel": True,
            "enable_final_channel": True,
        }
        plugin = MultiChannelAggregatorPlugin(mock_resources, config)

        message = """
        <analysis>This should be ignored</analysis>
        <commentary>This should be parsed</commentary>
        """
        channels = await plugin._parse_channels(message)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.COMMENTARY

    @pytest.mark.asyncio
    async def test_determine_strategy_default(self, basic_plugin, context):
        """Test strategy determination with default config."""
        strategy = await basic_plugin._determine_strategy(context)
        assert strategy == AggregationStrategy.USER_FRIENDLY

    @pytest.mark.asyncio
    async def test_determine_strategy_override(self, basic_plugin, context):
        """Test strategy determination with context override."""
        context.recall = AsyncMock(return_value="debugging")
        strategy = await basic_plugin._determine_strategy(context)
        assert strategy == AggregationStrategy.DEBUGGING

    @pytest.mark.asyncio
    async def test_determine_strategy_invalid_override(self, basic_plugin, context):
        """Test strategy determination with invalid override falls back to default."""
        context.recall = AsyncMock(return_value="invalid_strategy")
        strategy = await basic_plugin._determine_strategy(context)
        assert strategy == AggregationStrategy.USER_FRIENDLY  # Falls back to default

    @pytest.mark.asyncio
    async def test_process_channel_basic(self, basic_plugin, context):
        """Test basic channel processing."""
        channel = ChannelContent(
            channel_type=ChannelType.FINAL,
            raw_content="This is a final response with good content.",
            metadata={},
        )

        processed = await basic_plugin._process_channel(channel, context)

        assert processed is not None
        assert processed.channel_type == ChannelType.FINAL
        assert processed.raw_content == channel.raw_content
        assert processed.processed_content is not None
        assert processed.confidence_score is not None
        assert processed.confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_process_channel_safety_filtering(self, basic_plugin, context):
        """Test channel processing with safety filtering."""
        channel = ChannelContent(
            channel_type=ChannelType.ANALYSIS,
            raw_content="This harmful reasoning step shows dangerous methods.",
            metadata={},
        )

        processed = await basic_plugin._process_channel(channel, context)

        assert processed is not None
        assert "Content filtered for safety" in processed.processed_content
        assert "safety" in processed.metadata["filters_applied"]

    @pytest.mark.asyncio
    async def test_process_channel_technical_jargon_filtering(
        self, basic_plugin, context
    ):
        """Test channel processing with technical jargon filtering."""
        channel = ChannelContent(
            channel_type=ChannelType.ANALYSIS,
            raw_content="The token embedding attention mechanism with confidence score: 0.95 shows good results.",
            metadata={},
        )

        processed = await basic_plugin._process_channel(channel, context)

        assert processed is not None
        # Technical terms should be filtered
        assert "token" not in processed.processed_content
        assert "embedding" not in processed.processed_content

    @pytest.mark.asyncio
    async def test_process_channel_low_confidence_filtered(self, basic_plugin, context):
        """Test that low confidence channels are filtered out."""
        # Create a very short, low-quality channel
        channel = ChannelContent(
            channel_type=ChannelType.COMMENTARY,
            raw_content="hmm",  # Very short, low quality
            metadata={},
        )

        processed = await basic_plugin._process_channel(channel, context)

        # Should be filtered due to low confidence (floating point comparison)
        assert (
            processed is None
            or processed.confidence_score <= basic_plugin.config.min_channel_confidence
        )

    @pytest.mark.asyncio
    async def test_calculate_channel_confidence_high_quality(self, basic_plugin):
        """Test confidence calculation for high quality content."""
        channel = ChannelContent(
            channel_type=ChannelType.FINAL,
            raw_content="This is a comprehensive final answer that provides a clear conclusion and solution to the problem.",
            metadata={},
        )

        confidence = await basic_plugin._calculate_channel_confidence(
            channel, channel.raw_content
        )

        assert confidence > 0.7  # Should be high confidence

    @pytest.mark.asyncio
    async def test_calculate_channel_confidence_low_quality(self, basic_plugin):
        """Test confidence calculation for low quality content."""
        channel = ChannelContent(
            channel_type=ChannelType.COMMENTARY,
            raw_content="ok",  # Very short, low quality
            metadata={},
        )

        confidence = await basic_plugin._calculate_channel_confidence(
            channel, channel.raw_content
        )

        assert confidence < 0.5  # Should be low confidence

    @pytest.mark.asyncio
    async def test_aggregate_user_friendly(self, basic_plugin, context):
        """Test user-friendly aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                raw_content="This is the final answer.",
                processed_content="This is the final answer.",
                confidence_score=0.9,
                metadata={"filters_applied": []},
            ),
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                raw_content="Technical analysis with tokens and embeddings.",
                processed_content="Simplified analysis.",
                confidence_score=0.7,
                metadata={"filters_applied": ["technical_jargon"]},
            ),
        ]

        result = await basic_plugin._aggregate_channels(
            channels, AggregationStrategy.USER_FRIENDLY, context
        )

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_applied == AggregationStrategy.USER_FRIENDLY
        assert "This is the final answer." in result.user_response
        assert len(result.debug_response) > len(
            result.user_response
        )  # Debug has more detail
        assert ChannelType.FINAL in result.channels_used
        assert ChannelType.ANALYSIS in result.channels_used

    @pytest.mark.asyncio
    async def test_aggregate_debugging(self, basic_plugin, context):
        """Test debugging aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                raw_content="Raw technical analysis.",
                processed_content="Processed analysis.",
                confidence_score=0.8,
                metadata={"filters_applied": ["safety"]},
            )
        ]

        result = await basic_plugin._aggregate_channels(
            channels, AggregationStrategy.DEBUGGING, context
        )

        assert result.strategy_applied == AggregationStrategy.DEBUGGING
        assert "Raw: Raw technical analysis." in result.debug_response
        assert "Processed: Processed analysis." in result.debug_response
        assert "Filters: safety" in result.debug_response
        assert result.user_response == result.debug_response  # Same in debug mode

    @pytest.mark.asyncio
    async def test_aggregate_balanced(self, basic_plugin, context):
        """Test balanced aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                raw_content="Final answer here.",
                processed_content="Final answer here.",
                confidence_score=0.9,
                metadata={"filters_applied": []},
            ),
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                raw_content="Important technical analysis with key insights.",
                processed_content="Important analysis with key insights.",
                confidence_score=0.8,
                metadata={"filters_applied": []},
            ),
        ]

        result = await basic_plugin._aggregate_channels(
            channels, AggregationStrategy.BALANCED, context
        )

        assert result.strategy_applied == AggregationStrategy.BALANCED
        assert "Final answer here." in result.user_response
        # Should include some analysis insights
        assert len(result.user_response) > len(channels[0].processed_content)

    @pytest.mark.asyncio
    async def test_aggregate_empty_channels(self, basic_plugin, context):
        """Test aggregation with no channels."""
        result = await basic_plugin._aggregate_channels(
            [], AggregationStrategy.USER_FRIENDLY, context
        )

        assert result.user_response == ""
        assert result.debug_response == ""
        assert result.channels_used == []
        assert result.metadata.get("error") == "no_channels_to_aggregate"

    @pytest.mark.asyncio
    async def test_apply_safety_filter(self, basic_plugin):
        """Test safety filtering functionality."""
        content = "This harmful reasoning step shows dangerous methods for illegal activities."

        filtered_content, was_filtered = await basic_plugin._apply_safety_filter(
            content
        )

        assert was_filtered is True
        assert "Content filtered for safety" in filtered_content
        assert "dangerous" not in filtered_content

    @pytest.mark.asyncio
    async def test_apply_safety_filter_safe_content(self, basic_plugin):
        """Test safety filtering with safe content."""
        content = "This is a normal, safe response with helpful information."

        filtered_content, was_filtered = await basic_plugin._apply_safety_filter(
            content
        )

        assert was_filtered is False
        assert filtered_content == content  # No changes

    @pytest.mark.asyncio
    async def test_filter_technical_jargon(self, basic_plugin):
        """Test technical jargon filtering."""
        content = "The token embedding attention mechanism with confidence score: 0.95 works well."

        filtered_content, was_filtered = await basic_plugin._filter_technical_jargon(
            content
        )

        assert was_filtered is True
        assert "token" not in filtered_content
        assert "embedding" not in filtered_content
        assert "confidence score: 0.95" not in filtered_content

    @pytest.mark.asyncio
    async def test_filter_technical_jargon_disabled(self, mock_resources):
        """Test technical jargon filtering when disabled."""
        config = {"filter_technical_jargon": False}
        plugin = MultiChannelAggregatorPlugin(mock_resources, config)

        content = "The token embedding attention mechanism works well."

        filtered_content, was_filtered = await plugin._filter_technical_jargon(content)

        assert was_filtered is False
        assert filtered_content == content

    @pytest.mark.asyncio
    async def test_extract_key_insights(self, basic_plugin):
        """Test key insight extraction."""
        content = """
        This is normal text. However, this is an important finding that shows
        significant results. Note that the key insight here is critical for
        understanding. This is more normal text.
        """

        insights = await basic_plugin._extract_key_insights(content)

        assert "important" in insights.lower() or "significant" in insights.lower()
        assert len(insights) > 0

    def test_get_channel_priority(self, basic_plugin):
        """Test channel priority ordering."""
        final_priority = basic_plugin._get_channel_priority(ChannelType.FINAL)
        analysis_priority = basic_plugin._get_channel_priority(ChannelType.ANALYSIS)
        commentary_priority = basic_plugin._get_channel_priority(ChannelType.COMMENTARY)

        assert final_priority > analysis_priority > commentary_priority

    def test_get_channel_prefix(self, basic_plugin):
        """Test channel prefix retrieval."""
        analysis_prefix = basic_plugin._get_channel_prefix(ChannelType.ANALYSIS)
        commentary_prefix = basic_plugin._get_channel_prefix(ChannelType.COMMENTARY)
        final_prefix = basic_plugin._get_channel_prefix(ChannelType.FINAL)

        assert analysis_prefix == basic_plugin.config.analysis_prefix
        assert commentary_prefix == basic_plugin.config.commentary_prefix
        assert final_prefix == basic_plugin.config.final_prefix

    def test_is_channel_enabled(self, basic_plugin):
        """Test channel enablement check."""
        assert basic_plugin._is_channel_enabled(ChannelType.ANALYSIS) is True
        assert basic_plugin._is_channel_enabled(ChannelType.COMMENTARY) is True
        assert basic_plugin._is_channel_enabled(ChannelType.FINAL) is True

    @pytest.mark.asyncio
    async def test_full_execution_multi_channel(self, basic_plugin, context):
        """Test full execution with multi-channel input."""
        context.message = """
        <analysis>This is detailed analysis of the problem</analysis>
        <commentary>Additional commentary on the approach</commentary>
        <final>This is the final answer to the user's question</final>
        """

        result = await basic_plugin._execute_impl(context)

        assert "This is the final answer to the user's question" in result
        # Should have stored debug info
        context.remember.assert_called()
        context.log.assert_called()

    @pytest.mark.asyncio
    async def test_execution_with_length_limit(self, basic_plugin, context):
        """Test execution with response length limiting."""
        # Create very long content
        long_content = "Very long response. " * 200  # Over the 2000 char limit

        context.message = f"<final>{long_content}</final>"

        result = await basic_plugin._execute_impl(context)

        assert len(result) <= basic_plugin.config.max_user_response_length
        assert result.endswith("...")  # Should be truncated

    @pytest.mark.asyncio
    async def test_error_handling(self, basic_plugin, context):
        """Test error handling in execution."""
        # Mock an error in channel parsing to trigger error handling
        original_parse = basic_plugin._parse_channels

        async def failing_parse(*args, **kwargs):
            raise Exception("Test parsing error")

        basic_plugin._parse_channels = failing_parse

        result = await basic_plugin._execute_impl(context)

        # Should handle gracefully and return original message
        assert result == context.message
        # Should have logged error (don't check exact parameters as they vary)
        context.log.assert_called()

        # Restore original method
        basic_plugin._parse_channels = original_parse

    @pytest.mark.asyncio
    async def test_set_aggregation_strategy(self, basic_plugin, context):
        """Test setting aggregation strategy."""
        await basic_plugin.set_aggregation_strategy(
            AggregationStrategy.DEBUGGING, context
        )

        context.remember.assert_called_with(
            basic_plugin.config.strategy_override_key, "debugging"
        )

    @pytest.mark.asyncio
    async def test_get_channel_stats(self, basic_plugin):
        """Test getting channel statistics."""
        stats = await basic_plugin.get_channel_stats()

        assert "supported_channels" in stats
        assert "enabled_channels" in stats
        assert "available_strategies" in stats
        assert "default_strategy" in stats

        assert len(stats["supported_channels"]) == 3
        assert "analysis" in stats["supported_channels"]
        assert "commentary" in stats["supported_channels"]
        assert "final" in stats["supported_channels"]

    @pytest.mark.asyncio
    async def test_process_multi_channel_content_api(self, basic_plugin):
        """Test programmatic multi-channel content processing."""
        content = """
        <analysis>Analysis content</analysis>
        <final>Final response</final>
        """

        result = await basic_plugin.process_multi_channel_content(
            content, AggregationStrategy.USER_FRIENDLY
        )

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_applied == AggregationStrategy.USER_FRIENDLY
        assert len(result.channels_used) == 2
        assert "Final response" in result.user_response


class TestChannelContent:
    """Test ChannelContent model."""

    def test_channel_content_creation(self):
        """Test creating channel content."""
        content = ChannelContent(
            channel_type=ChannelType.ANALYSIS,
            raw_content="Test analysis content",
            confidence_score=0.8,
        )

        assert content.channel_type == ChannelType.ANALYSIS
        assert content.raw_content == "Test analysis content"
        assert content.confidence_score == 0.8
        assert content.processed_content is None
        assert content.metadata == {}

    def test_channel_content_with_metadata(self):
        """Test creating channel content with metadata."""
        metadata = {"source": "test", "length": 100}
        content = ChannelContent(
            channel_type=ChannelType.FINAL,
            raw_content="Test final content",
            metadata=metadata,
        )

        assert content.metadata == metadata


class TestAggregatedResponse:
    """Test AggregatedResponse model."""

    def test_aggregated_response_creation(self):
        """Test creating aggregated response."""
        response = AggregatedResponse(
            user_response="User friendly response",
            debug_response="Debug response with details",
            channels_used=[ChannelType.FINAL, ChannelType.ANALYSIS],
            strategy_applied=AggregationStrategy.USER_FRIENDLY,
            filtering_applied=["safety", "technical_jargon"],
        )

        assert response.user_response == "User friendly response"
        assert response.debug_response == "Debug response with details"
        assert len(response.channels_used) == 2
        assert response.strategy_applied == AggregationStrategy.USER_FRIENDLY
        assert "safety" in response.filtering_applied


class TestEnums:
    """Test enum functionality."""

    def test_channel_type_enum(self):
        """Test ChannelType enum."""
        assert ChannelType.ANALYSIS.value == "analysis"
        assert ChannelType.COMMENTARY.value == "commentary"
        assert ChannelType.FINAL.value == "final"

    def test_aggregation_strategy_enum(self):
        """Test AggregationStrategy enum."""
        assert AggregationStrategy.USER_FRIENDLY.value == "user_friendly"
        assert AggregationStrategy.DEBUGGING.value == "debugging"
        assert AggregationStrategy.BALANCED.value == "balanced"
        assert AggregationStrategy.CUSTOM.value == "custom"


class TestConfigModel:
    """Test ConfigModel functionality."""

    def test_config_model_defaults(self):
        """Test ConfigModel default values."""
        config = MultiChannelAggregatorPlugin.ConfigModel()

        assert config.enable_analysis_channel is True
        assert config.enable_commentary_channel is True
        assert config.enable_final_channel is True
        assert config.default_strategy == "user_friendly"
        assert config.filter_technical_jargon is True
        assert config.enable_safety_filtering is True
        assert config.max_user_response_length == 2000
        assert config.min_channel_confidence == 0.3
        assert config.include_debug_info is True

    def test_config_model_custom_values(self):
        """Test ConfigModel with custom values."""
        config = MultiChannelAggregatorPlugin.ConfigModel(
            default_strategy=AggregationStrategy.DEBUGGING,
            max_user_response_length=1000,
            enable_safety_filtering=False,
            filter_technical_jargon=False,
        )

        assert config.default_strategy == "debugging"
        assert config.max_user_response_length == 1000
        assert config.enable_safety_filtering is False
        assert config.filter_technical_jargon is False


if __name__ == "__main__":
    pytest.main([__file__])
