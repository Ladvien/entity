"""Multi-Channel Response Aggregator Plugin for GPT-OSS integration.

This plugin intelligently combines multi-channel outputs from gpt-oss (analysis,
commentary, final) into coherent user-friendly responses while preserving
technical details for logging and debugging.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class ChannelType(Enum):
    """Types of channels in GPT-OSS harmony format."""

    ANALYSIS = "analysis"
    COMMENTARY = "commentary"
    FINAL = "final"
    UNKNOWN = "unknown"


class AggregationStrategy(Enum):
    """Strategies for aggregating multi-channel responses."""

    VERBOSE = "verbose"  # Include all channels
    BALANCED = "balanced"  # Include final + selected analysis
    CONCISE = "concise"  # Only final output
    TECHNICAL = "technical"  # Analysis + commentary
    CUSTOM = "custom"  # User-defined rules


class ChannelContent(BaseModel):
    """Content from a single channel."""

    channel_type: ChannelType = Field(description="Type of channel")
    content: str = Field(description="Raw content from channel")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Channel metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    word_count: int = Field(default=0, description="Word count of content")
    has_technical_content: bool = Field(
        default=False, description="Whether content contains technical details"
    )
    safety_score: float = Field(
        default=1.0, description="Safety score (0-1, 1 being safest)", ge=0, le=1
    )


class AggregatedResponse(BaseModel):
    """Aggregated response from multiple channels."""

    user_output: str = Field(description="Final output for user")
    full_context: Dict[str, Any] = Field(description="Complete context for debugging")
    channels_used: List[ChannelType] = Field(
        description="Channels included in aggregation"
    )
    strategy_used: AggregationStrategy = Field(
        description="Aggregation strategy applied"
    )
    technical_summary: Optional[str] = Field(
        default=None, description="Technical summary for logging"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = Field(default=0, description="Time taken to aggregate")


class FormattingRule(BaseModel):
    """Rule for formatting channel content."""

    channel_type: ChannelType = Field(description="Channel to apply rule to")
    prefix: str = Field(default="", description="Prefix to add")
    suffix: str = Field(default="", description="Suffix to add")
    wrapper: Optional[str] = Field(
        default=None, description="Wrapper format (e.g., markdown)"
    )
    max_length: Optional[int] = Field(
        default=None, description="Maximum length for this channel"
    )
    include_metadata: bool = Field(
        default=False, description="Include channel metadata"
    )


class MultiChannelAggregatorPlugin(Plugin):
    """Plugin that aggregates multi-channel responses from GPT-OSS.

    This plugin:
    - Parses analysis, commentary, and final channels
    - Combines channels based on configurable strategies
    - Filters technical details from user-facing output
    - Preserves full context for debugging
    - Applies channel-specific formatting rules
    - Supports multiple aggregation strategies
    """

    supported_stages = [WorkflowExecutor.OUTPUT]
    dependencies = ["llm", "memory"]

    class ConfigModel(BaseModel):
        """Configuration for the multi-channel aggregator plugin."""

        # Aggregation settings
        default_strategy: AggregationStrategy = Field(
            default=AggregationStrategy.BALANCED,
            description="Default aggregation strategy",
        )
        allow_strategy_override: bool = Field(
            default=True,
            description="Allow runtime strategy override",
        )
        preserve_raw_channels: bool = Field(
            default=True,
            description="Store raw channel content in memory",
        )

        # Filtering settings
        filter_technical_details: bool = Field(
            default=True,
            description="Filter technical details from user output",
        )
        technical_keywords: List[str] = Field(
            default_factory=lambda: [
                "debug",
                "trace",
                "stack",
                "error",
                "exception",
                "implementation",
                "algorithm",
                "complexity",
            ],
            description="Keywords indicating technical content",
        )
        max_technical_percentage: float = Field(
            default=0.3,
            description="Max percentage of technical content in user output",
            ge=0,
            le=1,
        )

        # Channel processing
        channel_priority: List[ChannelType] = Field(
            default_factory=lambda: [
                ChannelType.FINAL,
                ChannelType.COMMENTARY,
                ChannelType.ANALYSIS,
            ],
            description="Priority order for channels",
        )
        require_final_channel: bool = Field(
            default=False,
            description="Require final channel to be present",
        )
        merge_similar_content: bool = Field(
            default=True,
            description="Merge similar content across channels",
        )

        # Formatting
        enable_formatting_rules: bool = Field(
            default=True,
            description="Apply formatting rules to channels",
        )
        default_formatting_rules: List[Dict[str, Any]] = Field(
            default_factory=lambda: [
                {
                    "channel_type": "analysis",
                    "prefix": "### Analysis:\n",
                    "wrapper": "markdown",
                },
                {
                    "channel_type": "commentary",
                    "prefix": "### Commentary:\n",
                    "wrapper": "markdown",
                },
                {
                    "channel_type": "final",
                    "prefix": "",
                    "wrapper": None,
                },
            ],
            description="Default formatting rules for channels",
        )

        # Output limits
        max_user_output_length: int = Field(
            default=4000,
            description="Maximum length for user output",
            ge=100,
            le=10000,
        )
        max_context_size_kb: int = Field(
            default=100,
            description="Maximum size for stored context in KB",
            ge=1,
            le=1000,
        )

        # Logging
        log_aggregation_decisions: bool = Field(
            default=True,
            description="Log aggregation decisions",
        )
        log_filtered_content: bool = Field(
            default=False,
            description="Log filtered technical content",
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the multi-channel aggregator plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize formatting rules
        self.formatting_rules = self._initialize_formatting_rules()

        # Channel parsing patterns
        self.channel_patterns = {
            ChannelType.ANALYSIS: re.compile(r"<analysis>(.*?)</analysis>", re.DOTALL),
            ChannelType.COMMENTARY: re.compile(
                r"<commentary>(.*?)</commentary>", re.DOTALL
            ),
            ChannelType.FINAL: re.compile(r"<final>(.*?)</final>", re.DOTALL),
        }

    async def _execute_impl(self, context) -> str:
        """Execute multi-channel aggregation in OUTPUT stage."""
        start_time = datetime.now()

        try:
            # Get the raw response from context
            raw_response = context.message

            # Parse channels from response
            channels = await self._parse_channels(raw_response)

            # Determine aggregation strategy
            strategy = await self._determine_strategy(context, channels)

            # Apply aggregation strategy
            aggregated = await self._aggregate_channels(channels, strategy, context)

            # Store full context if configured
            if self.config.preserve_raw_channels:
                await self._store_context(context, channels, aggregated)

            # Log aggregation decision
            if self.config.log_aggregation_decisions:
                await self._log_aggregation(context, aggregated)

            # Calculate processing time
            processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            aggregated.processing_time_ms = processing_time_ms

            return aggregated.user_output

        except Exception as e:
            # Log error and return original message
            await context.log(
                level="error",
                category="multi_channel_aggregator",
                message=f"Error in channel aggregation: {str(e)}",
                error=str(e),
            )
            return context.message

    async def _parse_channels(self, raw_response: str) -> List[ChannelContent]:
        """Parse channels from raw response."""
        channels = []

        for channel_type, pattern in self.channel_patterns.items():
            matches = pattern.findall(raw_response)
            for match in matches:
                content = match.strip()
                if content:
                    channel = ChannelContent(
                        channel_type=channel_type,
                        content=content,
                        word_count=len(content.split()),
                        has_technical_content=self._has_technical_content(content),
                        safety_score=await self._calculate_safety_score(content),
                    )
                    channels.append(channel)

        # If no channels found, treat entire response as final
        if not channels and raw_response.strip():
            channels.append(
                ChannelContent(
                    channel_type=ChannelType.FINAL,
                    content=raw_response.strip(),
                    word_count=len(raw_response.split()),
                    has_technical_content=self._has_technical_content(raw_response),
                )
            )

        return channels

    async def _determine_strategy(
        self, context, channels: List[ChannelContent]
    ) -> AggregationStrategy:
        """Determine aggregation strategy based on context and channels."""
        # Check for runtime override
        if self.config.allow_strategy_override:
            override = await context.recall("aggregation_strategy", None)
            if override:
                try:
                    return AggregationStrategy(override)
                except ValueError:
                    pass

        # Check if we have required channels
        channel_types = {c.channel_type for c in channels}

        # If only final channel, use concise
        if channel_types == {ChannelType.FINAL}:
            return AggregationStrategy.CONCISE

        # If heavy technical content, use technical strategy
        technical_ratio = sum(1 for c in channels if c.has_technical_content) / len(
            channels
        )
        if technical_ratio > 0.7:
            return AggregationStrategy.TECHNICAL

        # Default to configured strategy
        return self.config.default_strategy

    async def _aggregate_channels(
        self,
        channels: List[ChannelContent],
        strategy: AggregationStrategy,
        context,
    ) -> AggregatedResponse:
        """Aggregate channels based on strategy."""
        if strategy == AggregationStrategy.VERBOSE:
            return await self._aggregate_verbose(channels, context)
        elif strategy == AggregationStrategy.BALANCED:
            return await self._aggregate_balanced(channels, context)
        elif strategy == AggregationStrategy.CONCISE:
            return await self._aggregate_concise(channels, context)
        elif strategy == AggregationStrategy.TECHNICAL:
            return await self._aggregate_technical(channels, context)
        else:  # CUSTOM
            return await self._aggregate_custom(channels, context)

    async def _aggregate_verbose(
        self, channels: List[ChannelContent], context
    ) -> AggregatedResponse:
        """Verbose aggregation - include all channels."""
        output_parts = []
        channels_used = []

        # Sort channels by priority
        sorted_channels = sorted(
            channels,
            key=lambda c: (
                self.config.channel_priority.index(c.channel_type)
                if c.channel_type in self.config.channel_priority
                else len(self.config.channel_priority)
            ),
        )

        for channel in sorted_channels:
            formatted = await self._format_channel(channel)
            if formatted:
                output_parts.append(formatted)
                channels_used.append(channel.channel_type)

        user_output = "\n\n".join(output_parts)
        user_output = self._apply_output_limits(user_output)

        return AggregatedResponse(
            user_output=user_output,
            full_context={"channels": [c.model_dump() for c in channels]},
            channels_used=channels_used,
            strategy_used=AggregationStrategy.VERBOSE,
            technical_summary=self._create_technical_summary(channels),
        )

    async def _aggregate_balanced(
        self, channels: List[ChannelContent], context
    ) -> AggregatedResponse:
        """Balanced aggregation - final + selected analysis."""
        output_parts = []
        channels_used = []

        # Always include final channel if present
        final_channels = [c for c in channels if c.channel_type == ChannelType.FINAL]
        if final_channels:
            for channel in final_channels:
                formatted = await self._format_channel(channel)
                if formatted:
                    output_parts.append(formatted)
                    channels_used.append(ChannelType.FINAL)

        # Include non-technical analysis/commentary
        other_channels = [
            c
            for c in channels
            if c.channel_type != ChannelType.FINAL and not c.has_technical_content
        ]

        for channel in other_channels[:2]:  # Limit to 2 additional channels
            formatted = await self._format_channel(channel)
            if formatted:
                output_parts.append(formatted)
                channels_used.append(channel.channel_type)

        user_output = "\n\n".join(output_parts)
        user_output = self._apply_output_limits(user_output)

        return AggregatedResponse(
            user_output=user_output,
            full_context={"channels": [c.model_dump() for c in channels]},
            channels_used=channels_used,
            strategy_used=AggregationStrategy.BALANCED,
            technical_summary=self._create_technical_summary(channels),
        )

    async def _aggregate_concise(
        self, channels: List[ChannelContent], context
    ) -> AggregatedResponse:
        """Concise aggregation - only final output."""
        final_channels = [c for c in channels if c.channel_type == ChannelType.FINAL]

        if not final_channels:
            # Fall back to first available channel
            final_channels = channels[:1] if channels else []

        output_parts = []
        channels_used = []

        for channel in final_channels:
            # Don't apply formatting prefix/suffix for concise
            output_parts.append(channel.content)
            channels_used.append(channel.channel_type)

        user_output = "\n\n".join(output_parts)
        user_output = self._apply_output_limits(user_output)

        return AggregatedResponse(
            user_output=user_output,
            full_context={"channels": [c.model_dump() for c in channels]},
            channels_used=channels_used,
            strategy_used=AggregationStrategy.CONCISE,
            technical_summary=None,  # No technical summary for concise
        )

    async def _aggregate_technical(
        self, channels: List[ChannelContent], context
    ) -> AggregatedResponse:
        """Technical aggregation - analysis + commentary."""
        technical_channels = [
            c
            for c in channels
            if c.channel_type in [ChannelType.ANALYSIS, ChannelType.COMMENTARY]
        ]

        output_parts = []
        channels_used = []

        for channel in technical_channels:
            formatted = await self._format_channel(channel)
            if formatted:
                output_parts.append(formatted)
                channels_used.append(channel.channel_type)

        user_output = "\n\n".join(output_parts)
        user_output = self._apply_output_limits(user_output)

        return AggregatedResponse(
            user_output=user_output,
            full_context={"channels": [c.model_dump() for c in channels]},
            channels_used=channels_used,
            strategy_used=AggregationStrategy.TECHNICAL,
            technical_summary=self._create_technical_summary(channels),
        )

    async def _aggregate_custom(
        self, channels: List[ChannelContent], context
    ) -> AggregatedResponse:
        """Custom aggregation - user-defined rules."""
        # Load custom rules from context
        custom_rules = await context.recall("custom_aggregation_rules", {})

        output_parts = []
        channels_used = []

        # Apply custom rules
        for channel in channels:
            # Check if channel should be included based on custom rules
            include = custom_rules.get(channel.channel_type.value, {}).get(
                "include", True
            )
            if include:
                formatted = await self._format_channel(channel)
                if formatted:
                    output_parts.append(formatted)
                    channels_used.append(channel.channel_type)

        user_output = "\n\n".join(output_parts)
        user_output = self._apply_output_limits(user_output)

        return AggregatedResponse(
            user_output=user_output,
            full_context={
                "channels": [c.model_dump() for c in channels],
                "custom_rules": custom_rules,
            },
            channels_used=channels_used,
            strategy_used=AggregationStrategy.CUSTOM,
            technical_summary=self._create_technical_summary(channels),
        )

    async def _format_channel(self, channel: ChannelContent) -> str:
        """Apply formatting rules to a channel."""
        if not self.config.enable_formatting_rules:
            return channel.content

        # Find formatting rule for this channel
        rule = self.formatting_rules.get(channel.channel_type)
        if not rule:
            return channel.content

        formatted = channel.content

        # Apply max length if specified
        if rule.max_length and len(formatted) > rule.max_length:
            formatted = formatted[: rule.max_length] + "..."

        # Apply wrapper
        if rule.wrapper == "markdown":
            # Simple markdown formatting
            formatted = formatted.replace("\n", "\n> ")
            formatted = f"> {formatted}"

        # Apply prefix and suffix
        formatted = f"{rule.prefix}{formatted}{rule.suffix}"

        # Include metadata if requested
        if rule.include_metadata:
            metadata_str = f"\n_[{channel.channel_type.value} | {channel.word_count} words | safety: {channel.safety_score:.2f}]_"
            formatted += metadata_str

        return formatted

    def _has_technical_content(self, content: str) -> bool:
        """Check if content contains technical details."""
        if not self.config.filter_technical_details:
            return False

        content_lower = content.lower()
        technical_count = sum(
            1 for keyword in self.config.technical_keywords if keyword in content_lower
        )

        # Check for code blocks
        if "```" in content or "def " in content or "class " in content:
            technical_count += 3

        # Check for stack traces
        if "traceback" in content_lower or "exception" in content_lower:
            technical_count += 2

        word_count = len(content.split())
        if word_count > 0:
            technical_ratio = technical_count / word_count
            return technical_ratio > self.config.max_technical_percentage

        return False

    async def _calculate_safety_score(self, content: str) -> float:
        """Calculate safety score for content."""
        # Simplified safety scoring
        unsafe_patterns = [
            "error",
            "exception",
            "fatal",
            "critical",
            "warning",
            "deprecated",
        ]

        content_lower = content.lower()
        unsafe_count = sum(1 for pattern in unsafe_patterns if pattern in content_lower)

        # Calculate score (1.0 is safest)
        if unsafe_count == 0:
            return 1.0
        elif unsafe_count <= 2:
            return 0.8
        elif unsafe_count <= 5:
            return 0.6
        else:
            return 0.4

    def _apply_output_limits(self, output: str) -> str:
        """Apply output length limits."""
        if len(output) > self.config.max_user_output_length:
            # Truncate intelligently at sentence boundary
            truncated = output[: self.config.max_user_output_length]
            last_period = truncated.rfind(".")
            if last_period > self.config.max_user_output_length * 0.8:
                truncated = truncated[: last_period + 1]
            else:
                truncated += "..."
            return truncated
        return output

    def _create_technical_summary(
        self, channels: List[ChannelContent]
    ) -> Optional[str]:
        """Create technical summary from channels."""
        technical_channels = [c for c in channels if c.has_technical_content]
        if not technical_channels:
            return None

        summary_parts = []
        for channel in technical_channels:
            summary = f"[{channel.channel_type.value}]: {channel.content[:200]}..."
            summary_parts.append(summary)

        return "\n".join(summary_parts)

    async def _store_context(
        self,
        context,
        channels: List[ChannelContent],
        aggregated: AggregatedResponse,
    ) -> None:
        """Store full context for debugging."""
        # Convert to JSON-serializable format
        channels_data = []
        for c in channels:
            channel_dict = c.model_dump(mode="json")
            # Ensure channel_type is string
            channel_dict["channel_type"] = c.channel_type.value
            channels_data.append(channel_dict)

        aggregation_dict = aggregated.model_dump(mode="json")
        # Ensure enums are strings
        aggregation_dict["strategy_used"] = aggregated.strategy_used.value
        aggregation_dict["channels_used"] = [
            ch.value for ch in aggregated.channels_used
        ]

        context_data = {
            "timestamp": datetime.now().isoformat(),
            "channels": channels_data,
            "aggregation": aggregation_dict,
            "strategy": aggregated.strategy_used.value,
            "processing_time_ms": aggregated.processing_time_ms,
        }

        # Check size limit
        import json

        context_size_kb = len(json.dumps(context_data)) / 1024
        if context_size_kb > self.config.max_context_size_kb:
            # Truncate channel content
            for channel_data in context_data["channels"]:
                if len(channel_data["content"]) > 1000:
                    channel_data["content"] = channel_data["content"][:1000] + "..."

        await context.remember(
            f"channel_aggregation:{context.execution_id}", context_data
        )

    async def _log_aggregation(self, context, aggregated: AggregatedResponse) -> None:
        """Log aggregation decision."""
        await context.log(
            level="info",
            category="multi_channel_aggregator",
            message="Channel aggregation completed",
            strategy=aggregated.strategy_used.value,
            channels_used=[c.value for c in aggregated.channels_used],
            processing_time_ms=aggregated.processing_time_ms,
            output_length=len(aggregated.user_output),
        )

        if self.config.log_filtered_content and aggregated.technical_summary:
            await context.log(
                level="debug",
                category="multi_channel_aggregator",
                message="Technical content filtered",
                technical_summary=aggregated.technical_summary[:500],
            )

    def _initialize_formatting_rules(self) -> Dict[ChannelType, FormattingRule]:
        """Initialize formatting rules from config."""
        rules = {}
        for rule_config in self.config.default_formatting_rules:
            try:
                channel_type = ChannelType(rule_config.get("channel_type"))
                rule = FormattingRule(
                    channel_type=channel_type,
                    prefix=rule_config.get("prefix", ""),
                    suffix=rule_config.get("suffix", ""),
                    wrapper=rule_config.get("wrapper"),
                    max_length=rule_config.get("max_length"),
                    include_metadata=rule_config.get("include_metadata", False),
                )
                rules[channel_type] = rule
            except (ValueError, KeyError):
                continue
        return rules

    # Public API methods

    async def set_aggregation_strategy(
        self, context, strategy: AggregationStrategy
    ) -> None:
        """Set aggregation strategy for current context."""
        await context.remember("aggregation_strategy", strategy.value)

    async def set_custom_rules(self, context, rules: Dict[str, Any]) -> None:
        """Set custom aggregation rules."""
        await context.remember("custom_aggregation_rules", rules)

    async def get_channel_metrics(self, context) -> Dict[str, Any]:
        """Get metrics about channel usage."""
        # Load recent aggregations
        metrics = {
            "total_aggregations": 0,
            "strategy_distribution": {},
            "channel_frequency": {},
            "average_processing_time_ms": 0,
        }

        # This would typically load from memory/database
        # For now, return empty metrics
        return metrics
