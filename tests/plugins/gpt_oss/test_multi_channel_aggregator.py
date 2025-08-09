"""Unit tests for Multi-Channel Response Aggregator Plugin."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.multi_channel_aggregator import (
    AggregatedResponse,
    AggregationStrategy,
    ChannelContent,
    ChannelType,
    FormattingRule,
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
            "default_strategy": AggregationStrategy.BALANCED.value,
            "filter_technical_details": True,
            "preserve_raw_channels": True,
        }
        return MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.fixture
    def verbose_plugin(self, mock_resources):
        """Create plugin configured for verbose output."""
        config = {
            "default_strategy": AggregationStrategy.VERBOSE.value,
            "filter_technical_details": False,
            "enable_formatting_rules": True,
        }
        return MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.fixture
    def concise_plugin(self, mock_resources):
        """Create plugin configured for concise output."""
        config = {
            "default_strategy": AggregationStrategy.CONCISE.value,
            "filter_technical_details": True,
            "require_final_channel": True,
        }
        return MultiChannelAggregatorPlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.OUTPUT
        ctx.message = "Test message"
        ctx.execution_id = "test_exec_123"
        ctx.remember = AsyncMock()
        ctx.recall = AsyncMock(return_value=None)
        ctx.log = AsyncMock()
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.default_strategy == AggregationStrategy.BALANCED
        assert basic_plugin.config.filter_technical_details is True
        assert WorkflowExecutor.OUTPUT in basic_plugin.supported_stages
        assert "llm" in basic_plugin.dependencies
        assert "memory" in basic_plugin.dependencies

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"max_user_output_length": -1}  # Invalid negative value

        with pytest.raises(ValueError, match="Invalid configuration"):
            MultiChannelAggregatorPlugin(mock_resources, config)

    def test_formatting_rules_initialization(self, basic_plugin):
        """Test that formatting rules are properly initialized."""
        assert len(basic_plugin.formatting_rules) > 0
        assert ChannelType.FINAL in basic_plugin.formatting_rules
        assert ChannelType.ANALYSIS in basic_plugin.formatting_rules
        assert ChannelType.COMMENTARY in basic_plugin.formatting_rules

    @pytest.mark.asyncio
    async def test_basic_execution(self, basic_plugin, context):
        """Test basic plugin execution."""
        context.message = "<final>This is the final output.</final>"
        result = await basic_plugin._execute_impl(context)

        assert "This is the final output." in result
        # Should store context if preserve_raw_channels is True
        if basic_plugin.config.preserve_raw_channels:
            context.remember.assert_called()

    @pytest.mark.asyncio
    async def test_parse_channels_single(self, basic_plugin):
        """Test parsing single channel."""
        raw = "<final>Final content</final>"
        channels = await basic_plugin._parse_channels(raw)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.FINAL
        assert channels[0].content == "Final content"

    @pytest.mark.asyncio
    async def test_parse_channels_multiple(self, basic_plugin):
        """Test parsing multiple channels."""
        raw = """
        <analysis>Analysis content</analysis>
        <commentary>Commentary content</commentary>
        <final>Final content</final>
        """
        channels = await basic_plugin._parse_channels(raw)

        assert len(channels) == 3
        channel_types = {c.channel_type for c in channels}
        assert ChannelType.ANALYSIS in channel_types
        assert ChannelType.COMMENTARY in channel_types
        assert ChannelType.FINAL in channel_types

    @pytest.mark.asyncio
    async def test_parse_channels_no_tags(self, basic_plugin):
        """Test parsing when no channel tags present."""
        raw = "Plain text without channel tags"
        channels = await basic_plugin._parse_channels(raw)

        assert len(channels) == 1
        assert channels[0].channel_type == ChannelType.FINAL
        assert channels[0].content == raw.strip()

    @pytest.mark.asyncio
    async def test_parse_channels_empty(self, basic_plugin):
        """Test parsing empty response."""
        channels = await basic_plugin._parse_channels("")
        assert len(channels) == 0

    @pytest.mark.asyncio
    async def test_determine_strategy_default(self, basic_plugin, context):
        """Test default strategy determination."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Analysis",
                has_technical_content=False,
            ),
        ]

        strategy = await basic_plugin._determine_strategy(context, channels)
        assert strategy == AggregationStrategy.BALANCED

    @pytest.mark.asyncio
    async def test_determine_strategy_override(self, basic_plugin, context):
        """Test strategy override from context."""
        context.recall = AsyncMock(return_value="verbose")
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final",
                has_technical_content=False,
            )
        ]

        strategy = await basic_plugin._determine_strategy(context, channels)
        assert strategy == AggregationStrategy.VERBOSE

    @pytest.mark.asyncio
    async def test_determine_strategy_technical(self, basic_plugin, context):
        """Test technical strategy selection."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Technical",
                has_technical_content=True,
            ),
            ChannelContent(
                channel_type=ChannelType.COMMENTARY,
                content="Technical",
                has_technical_content=True,
            ),
        ]

        strategy = await basic_plugin._determine_strategy(context, channels)
        assert strategy == AggregationStrategy.TECHNICAL

    @pytest.mark.asyncio
    async def test_determine_strategy_concise_only_final(self, basic_plugin, context):
        """Test concise strategy when only final channel."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final only",
                has_technical_content=False,
            )
        ]

        strategy = await basic_plugin._determine_strategy(context, channels)
        assert strategy == AggregationStrategy.CONCISE

    @pytest.mark.asyncio
    async def test_aggregate_verbose(self, verbose_plugin, context):
        """Test verbose aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Analysis content",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.COMMENTARY,
                content="Commentary content",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final content",
                has_technical_content=False,
            ),
        ]

        result = await verbose_plugin._aggregate_verbose(channels, context)

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_used == AggregationStrategy.VERBOSE
        assert len(result.channels_used) == 3
        assert "Final content" in result.user_output
        assert "Analysis content" in result.user_output
        assert "Commentary content" in result.user_output

    @pytest.mark.asyncio
    async def test_aggregate_balanced(self, basic_plugin, context):
        """Test balanced aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Technical analysis",
                has_technical_content=True,
            ),
            ChannelContent(
                channel_type=ChannelType.COMMENTARY,
                content="User-friendly commentary",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final output",
                has_technical_content=False,
            ),
        ]

        result = await basic_plugin._aggregate_balanced(channels, context)

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_used == AggregationStrategy.BALANCED
        assert ChannelType.FINAL in result.channels_used
        assert "Final output" in result.user_output
        # Technical analysis should be filtered out
        assert "Technical analysis" not in result.user_output

    @pytest.mark.asyncio
    async def test_aggregate_concise(self, concise_plugin, context):
        """Test concise aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Analysis",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final output only",
                has_technical_content=False,
            ),
        ]

        result = await concise_plugin._aggregate_concise(channels, context)

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_used == AggregationStrategy.CONCISE
        assert len(result.channels_used) == 1
        assert result.channels_used[0] == ChannelType.FINAL
        assert result.user_output == "Final output only"
        assert "Analysis" not in result.user_output

    @pytest.mark.asyncio
    async def test_aggregate_technical(self, basic_plugin, context):
        """Test technical aggregation strategy."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Technical analysis",
                has_technical_content=True,
            ),
            ChannelContent(
                channel_type=ChannelType.COMMENTARY,
                content="Technical commentary",
                has_technical_content=True,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="User output",
                has_technical_content=False,
            ),
        ]

        result = await basic_plugin._aggregate_technical(channels, context)

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_used == AggregationStrategy.TECHNICAL
        assert ChannelType.ANALYSIS in result.channels_used
        assert ChannelType.COMMENTARY in result.channels_used
        assert ChannelType.FINAL not in result.channels_used
        assert result.technical_summary is not None

    @pytest.mark.asyncio
    async def test_aggregate_custom(self, basic_plugin, context):
        """Test custom aggregation strategy."""
        # Set custom rules
        context.recall = AsyncMock(
            return_value={
                "analysis": {"include": False},
                "commentary": {"include": True},
                "final": {"include": True},
            }
        )

        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Analysis",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.COMMENTARY,
                content="Commentary",
                has_technical_content=False,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Final",
                has_technical_content=False,
            ),
        ]

        result = await basic_plugin._aggregate_custom(channels, context)

        assert isinstance(result, AggregatedResponse)
        assert result.strategy_used == AggregationStrategy.CUSTOM
        # Analysis should be excluded
        assert ChannelType.ANALYSIS not in result.channels_used
        assert ChannelType.COMMENTARY in result.channels_used
        assert ChannelType.FINAL in result.channels_used

    @pytest.mark.asyncio
    async def test_format_channel_with_rules(self, verbose_plugin):
        """Test channel formatting with rules."""
        channel = ChannelContent(
            channel_type=ChannelType.ANALYSIS,
            content="Test content",
            has_technical_content=False,
        )

        formatted = await verbose_plugin._format_channel(channel)

        assert "### Analysis:" in formatted
        assert "Test content" in formatted

    @pytest.mark.asyncio
    async def test_format_channel_max_length(self, basic_plugin):
        """Test channel formatting with max length."""
        rule = FormattingRule(
            channel_type=ChannelType.ANALYSIS,
            prefix="",
            max_length=10,
        )
        basic_plugin.formatting_rules[ChannelType.ANALYSIS] = rule

        channel = ChannelContent(
            channel_type=ChannelType.ANALYSIS,
            content="This is a very long content that should be truncated",
            has_technical_content=False,
        )

        formatted = await basic_plugin._format_channel(channel)

        assert len(formatted) <= 13  # 10 + "..."
        assert "..." in formatted

    @pytest.mark.asyncio
    async def test_format_channel_with_metadata(self, basic_plugin):
        """Test channel formatting with metadata."""
        rule = FormattingRule(
            channel_type=ChannelType.FINAL,
            prefix="",
            include_metadata=True,
        )
        basic_plugin.formatting_rules[ChannelType.FINAL] = rule

        channel = ChannelContent(
            channel_type=ChannelType.FINAL,
            content="Content",
            word_count=1,
            safety_score=0.95,
            has_technical_content=False,
        )

        formatted = await basic_plugin._format_channel(channel)

        assert "final" in formatted
        assert "1 words" in formatted
        assert "0.95" in formatted

    def test_has_technical_content_positive(self, basic_plugin):
        """Test technical content detection."""
        content = (
            "This contains debug information and stack trace with algorithm details"
        )
        result = basic_plugin._has_technical_content(content)
        assert result is True

    def test_has_technical_content_negative(self, basic_plugin):
        """Test non-technical content detection."""
        content = "This is a simple user-friendly message"
        result = basic_plugin._has_technical_content(content)
        assert result is False

    def test_has_technical_content_code_blocks(self, basic_plugin):
        """Test technical content detection with code."""
        content = "```python\ndef test():\n    pass\n```"
        result = basic_plugin._has_technical_content(content)
        assert result is True

    @pytest.mark.asyncio
    async def test_calculate_safety_score_safe(self, basic_plugin):
        """Test safety score calculation for safe content."""
        score = await basic_plugin._calculate_safety_score("This is safe content")
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_calculate_safety_score_warnings(self, basic_plugin):
        """Test safety score calculation with warnings."""
        score = await basic_plugin._calculate_safety_score(
            "Warning: deprecated function"
        )
        assert score < 1.0
        assert score >= 0.4

    @pytest.mark.asyncio
    async def test_calculate_safety_score_errors(self, basic_plugin):
        """Test safety score calculation with errors."""
        score = await basic_plugin._calculate_safety_score(
            "Fatal error exception critical warning deprecated"
        )
        assert score < 0.8

    def test_apply_output_limits(self, basic_plugin):
        """Test output length limiting."""
        basic_plugin.config.max_user_output_length = 50
        long_text = "a" * 100
        limited = basic_plugin._apply_output_limits(long_text)

        assert len(limited) <= 53  # 50 + "..."

    def test_apply_output_limits_sentence_boundary(self, basic_plugin):
        """Test output limiting at sentence boundary."""
        basic_plugin.config.max_user_output_length = 50
        text = "This is a sentence. Another sentence. Final one here that is long."
        limited = basic_plugin._apply_output_limits(text)

        # Should truncate at sentence boundary if possible
        assert limited.endswith(".") or limited.endswith("...")

    def test_create_technical_summary(self, basic_plugin):
        """Test technical summary creation."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.ANALYSIS,
                content="Technical analysis details that are very long and complex",
                has_technical_content=True,
            ),
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Simple output",
                has_technical_content=False,
            ),
        ]

        summary = basic_plugin._create_technical_summary(channels)

        assert summary is not None
        assert "[analysis]:" in summary
        assert "Technical analysis" in summary
        assert "Simple output" not in summary

    def test_create_technical_summary_none(self, basic_plugin):
        """Test technical summary when no technical content."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Simple output",
                has_technical_content=False,
            )
        ]

        summary = basic_plugin._create_technical_summary(channels)
        assert summary is None

    @pytest.mark.asyncio
    async def test_store_context(self, basic_plugin, context):
        """Test context storage."""
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content="Test",
                has_technical_content=False,
            )
        ]
        aggregated = AggregatedResponse(
            user_output="Test",
            full_context={},
            channels_used=[ChannelType.FINAL],
            strategy_used=AggregationStrategy.CONCISE,
            processing_time_ms=10.5,
        )

        await basic_plugin._store_context(context, channels, aggregated)

        context.remember.assert_called()
        call_args = context.remember.call_args[0]
        assert "channel_aggregation:test_exec_123" == call_args[0]
        stored_data = call_args[1]
        assert "timestamp" in stored_data
        assert "channels" in stored_data
        assert "aggregation" in stored_data

    @pytest.mark.asyncio
    async def test_store_context_size_limit(self, basic_plugin, context):
        """Test context storage with size limit."""
        basic_plugin.config.max_context_size_kb = 1  # Very small limit

        # Create large content
        large_content = "x" * 10000
        channels = [
            ChannelContent(
                channel_type=ChannelType.FINAL,
                content=large_content,
                has_technical_content=False,
            )
        ]
        aggregated = AggregatedResponse(
            user_output="Test",
            full_context={},
            channels_used=[ChannelType.FINAL],
            strategy_used=AggregationStrategy.CONCISE,
        )

        await basic_plugin._store_context(context, channels, aggregated)

        # Should truncate content
        context.remember.assert_called()
        stored_data = context.remember.call_args[0][1]
        stored_content = stored_data["channels"][0]["content"]
        assert len(stored_content) < len(large_content)
        assert "..." in stored_content

    @pytest.mark.asyncio
    async def test_log_aggregation(self, basic_plugin, context):
        """Test aggregation logging."""
        aggregated = AggregatedResponse(
            user_output="Test output",
            full_context={},
            channels_used=[ChannelType.FINAL],
            strategy_used=AggregationStrategy.BALANCED,
            processing_time_ms=15.5,
        )

        await basic_plugin._log_aggregation(context, aggregated)

        context.log.assert_called()
        log_call = context.log.call_args[1]
        assert log_call["level"] == "info"
        assert log_call["strategy"] == "balanced"
        assert log_call["processing_time_ms"] == 15.5

    @pytest.mark.asyncio
    async def test_log_aggregation_with_technical(self, basic_plugin, context):
        """Test aggregation logging with technical content."""
        basic_plugin.config.log_filtered_content = True
        aggregated = AggregatedResponse(
            user_output="Test",
            full_context={},
            channels_used=[ChannelType.FINAL],
            strategy_used=AggregationStrategy.BALANCED,
            technical_summary="Technical details here",
        )

        await basic_plugin._log_aggregation(context, aggregated)

        # Should have two log calls
        assert context.log.call_count == 2
        # Second call should be debug level with technical summary
        second_call = context.log.call_args_list[1][1]
        assert second_call["level"] == "debug"
        assert "Technical details" in second_call["technical_summary"]

    @pytest.mark.asyncio
    async def test_error_handling(self, basic_plugin, context):
        """Test error handling in execution."""
        # Create invalid response that will cause parsing error
        context.message = None

        result = await basic_plugin._execute_impl(context)

        # Should return original message on error
        assert result == context.message
        context.log.assert_called()
        log_call = context.log.call_args[1]
        assert log_call["level"] == "error"

    @pytest.mark.asyncio
    async def test_set_aggregation_strategy(self, basic_plugin, context):
        """Test setting aggregation strategy."""
        await basic_plugin.set_aggregation_strategy(
            context, AggregationStrategy.VERBOSE
        )

        context.remember.assert_called_with("aggregation_strategy", "verbose")

    @pytest.mark.asyncio
    async def test_set_custom_rules(self, basic_plugin, context):
        """Test setting custom aggregation rules."""
        rules = {"analysis": {"include": False}}
        await basic_plugin.set_custom_rules(context, rules)

        context.remember.assert_called_with("custom_aggregation_rules", rules)

    @pytest.mark.asyncio
    async def test_get_channel_metrics(self, basic_plugin, context):
        """Test getting channel metrics."""
        metrics = await basic_plugin.get_channel_metrics(context)

        assert isinstance(metrics, dict)
        assert "total_aggregations" in metrics
        assert "strategy_distribution" in metrics
        assert "channel_frequency" in metrics
        assert "average_processing_time_ms" in metrics

    def test_channel_type_enum(self):
        """Test ChannelType enum."""
        assert ChannelType.ANALYSIS.value == "analysis"
        assert ChannelType.COMMENTARY.value == "commentary"
        assert ChannelType.FINAL.value == "final"
        assert ChannelType.UNKNOWN.value == "unknown"

    def test_aggregation_strategy_enum(self):
        """Test AggregationStrategy enum."""
        assert AggregationStrategy.VERBOSE.value == "verbose"
        assert AggregationStrategy.BALANCED.value == "balanced"
        assert AggregationStrategy.CONCISE.value == "concise"
        assert AggregationStrategy.TECHNICAL.value == "technical"
        assert AggregationStrategy.CUSTOM.value == "custom"

    def test_channel_content_model(self):
        """Test ChannelContent model."""
        content = ChannelContent(
            channel_type=ChannelType.FINAL,
            content="Test content",
            word_count=2,
            has_technical_content=False,
            safety_score=0.95,
        )

        assert content.channel_type == ChannelType.FINAL
        assert content.content == "Test content"
        assert content.safety_score == 0.95
        assert content.has_technical_content is False

    def test_aggregated_response_model(self):
        """Test AggregatedResponse model."""
        response = AggregatedResponse(
            user_output="User output",
            full_context={"test": "data"},
            channels_used=[ChannelType.FINAL],
            strategy_used=AggregationStrategy.BALANCED,
            technical_summary="Tech summary",
            processing_time_ms=12.5,
        )

        assert response.user_output == "User output"
        assert response.strategy_used == AggregationStrategy.BALANCED
        assert response.processing_time_ms == 12.5
        assert response.technical_summary == "Tech summary"

    def test_formatting_rule_model(self):
        """Test FormattingRule model."""
        rule = FormattingRule(
            channel_type=ChannelType.ANALYSIS,
            prefix="### ",
            suffix="\n",
            wrapper="markdown",
            max_length=1000,
            include_metadata=True,
        )

        assert rule.channel_type == ChannelType.ANALYSIS
        assert rule.prefix == "### "
        assert rule.wrapper == "markdown"
        assert rule.include_metadata is True

    def test_supported_stages(self, basic_plugin):
        """Test that plugin only supports OUTPUT stage."""
        assert basic_plugin.supported_stages == [WorkflowExecutor.OUTPUT]

    def test_required_dependencies(self, basic_plugin):
        """Test that plugin declares correct dependencies."""
        assert "llm" in basic_plugin.dependencies
        assert "memory" in basic_plugin.dependencies

    @pytest.mark.asyncio
    async def test_multi_channel_integration(self, basic_plugin, context):
        """Test complete multi-channel integration."""
        # Create a complex multi-channel response
        context.message = """
        <analysis>
        This is the technical analysis of the problem.
        It contains debug information and implementation details.
        </analysis>

        <commentary>
        Here's some developer commentary about the approach.
        </commentary>

        <final>
        This is the user-friendly final output that explains the solution clearly.
        </final>
        """

        result = await basic_plugin._execute_impl(context)

        # Should use balanced strategy and include final
        assert "user-friendly final output" in result
        # Should also include commentary as it's not technical
        assert "developer commentary" in result

        # Verify context was stored
        context.remember.assert_called()
        stored_key = context.remember.call_args[0][0]
        assert "channel_aggregation:" in stored_key
