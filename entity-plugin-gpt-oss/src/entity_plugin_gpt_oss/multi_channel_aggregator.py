"""Multi-Channel Response Aggregator Plugin for GPT-OSS Integration.

This plugin intelligently combines multi-channel outputs from gpt-oss
(analysis, commentary, final) into coherent user-friendly responses while
preserving technical details for debugging and logging purposes.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor
from pydantic import BaseModel, Field


class ChannelType(Enum):
    """Types of channels in gpt-oss multi-channel output."""

    ANALYSIS = "analysis"
    COMMENTARY = "commentary"
    FINAL = "final"


class AggregationStrategy(Enum):
    """Strategies for aggregating multi-channel content."""

    USER_FRIENDLY = "user_friendly"  # Clean, user-facing output
    DEBUGGING = "debugging"  # Full technical context preserved
    BALANCED = "balanced"  # Mix of user-friendly with key technical insights
    CUSTOM = "custom"  # Custom strategy based on configuration


class ChannelContent(BaseModel):
    """Represents content from a specific channel."""

    channel_type: ChannelType = Field(description="Type of channel")
    raw_content: str = Field(description="Raw content from channel")
    processed_content: str | None = Field(
        default=None, description="Processed/filtered content"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Channel-specific metadata"
    )
    confidence_score: float | None = Field(
        default=None, description="Confidence in content quality", ge=0.0, le=1.0
    )


class AggregatedResponse(BaseModel):
    """Represents an aggregated multi-channel response."""

    user_response: str = Field(description="User-facing response")
    debug_response: str = Field(description="Full response for debugging")
    channels_used: list[ChannelType] = Field(
        description="Channels included in aggregation"
    )
    strategy_applied: AggregationStrategy = Field(
        description="Aggregation strategy used"
    )
    filtering_applied: list[str] = Field(
        default_factory=list, description="List of filters applied"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Aggregation metadata"
    )


class MultiChannelAggregatorPlugin(Plugin):
    """Plugin that aggregates multi-channel responses from gpt-oss.

    This plugin runs in the REVIEW stage to process multi-channel outputs
    from gpt-oss, combining analysis, commentary, and final response channels
    into coherent user-friendly outputs while preserving technical context.
    """

    supported_stages = [WorkflowExecutor.REVIEW]

    class ConfigModel(BaseModel):
        """Configuration for the multi-channel aggregator plugin."""

        # Channel processing
        enable_analysis_channel: bool = Field(
            default=True, description="Enable processing of analysis channel"
        )
        enable_commentary_channel: bool = Field(
            default=True, description="Enable processing of commentary channel"
        )
        enable_final_channel: bool = Field(
            default=True, description="Enable processing of final channel"
        )

        # Aggregation strategy
        default_strategy: str = Field(
            default=AggregationStrategy.USER_FRIENDLY.value,
            description="Default aggregation strategy",
        )
        strategy_override_key: str = Field(
            default="aggregation_strategy",
            description="Context key for strategy override",
        )

        # Content filtering
        filter_technical_jargon: bool = Field(
            default=True, description="Filter technical jargon from user response"
        )
        filter_reasoning_steps: bool = Field(
            default=True,
            description="Filter detailed reasoning steps from user response",
        )
        filter_confidence_markers: bool = Field(
            default=True, description="Filter confidence markers from user response"
        )
        preserve_key_insights: bool = Field(
            default=True, description="Preserve key insights even when filtering"
        )

        # Safety and quality
        enable_safety_filtering: bool = Field(
            default=True, description="Enable safety content filtering"
        )
        min_channel_confidence: float = Field(
            default=0.3,
            description="Minimum confidence to include channel",
            ge=0.0,
            le=1.0,
        )
        max_user_response_length: int = Field(
            default=2000, description="Maximum length of user-facing response", ge=100
        )

        # Formatting rules
        analysis_prefix: str = Field(
            default="[Analysis]", description="Prefix for analysis content"
        )
        commentary_prefix: str = Field(
            default="[Commentary]", description="Prefix for commentary content"
        )
        final_prefix: str = Field(
            default="[Final]", description="Prefix for final content"
        )

        # Debug settings
        include_debug_info: bool = Field(
            default=True, description="Include debug information in response"
        )
        log_channel_processing: bool = Field(
            default=True, description="Log channel processing details"
        )
        preserve_original_formatting: bool = Field(
            default=False, description="Preserve original channel formatting"
        )

        class Config:
            use_enum_values = True

    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize the multi-channel aggregator plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize channel patterns
        self._channel_patterns = {
            ChannelType.ANALYSIS: [
                r"<analysis>(.*?)</analysis>",
                r"\[ANALYSIS\](.*?)\[/ANALYSIS\]",
                r"Analysis:(.*?)(?=Commentary:|Final:|$)",
            ],
            ChannelType.COMMENTARY: [
                r"<commentary>(.*?)</commentary>",
                r"\[COMMENTARY\](.*?)\[/COMMENTARY\]",
                r"Commentary:(.*?)(?=Analysis:|Final:|$)",
            ],
            ChannelType.FINAL: [
                r"<final>(.*?)</final>",
                r"\[FINAL\](.*?)\[/FINAL\]",
                r"Final:(.*?)(?=Analysis:|Commentary:|$)",
            ],
        }

        # Initialize safety patterns (content to filter)
        self._safety_patterns = [
            r"(?i)\b(harmful|dangerous|illegal|unethical)\b.*?reasoning",
            r"(?i)step-by-step.*?exploit",
            r"(?i)detailed.*?bypass.*?safety",
        ]

        # Initialize technical jargon patterns
        self._technical_patterns = [
            r"\b(?:token|embedding|attention|transformer|logit|softmax)\b",
            r"\bconfidence\s+(?:score|level|threshold):\s*[\d.]+\b",
            r"\b(?:reasoning|inference)\s+(?:step|chain|process)\s*\d+\b",
        ]

    async def _execute_impl(self, context) -> str:
        """Execute multi-channel aggregation.

        Args:
            context: Plugin execution context

        Returns:
            Aggregated response string
        """
        try:
            # Parse multi-channel content from message
            channels = await self._parse_channels(context.message)

            if not channels:
                # No multi-channel content detected, pass through
                return context.message

            # Determine aggregation strategy
            strategy = await self._determine_strategy(context)

            # Process each channel
            processed_channels = []
            for channel in channels:
                processed = await self._process_channel(channel, context)
                if processed:
                    processed_channels.append(processed)

            # Aggregate channels
            aggregated = await self._aggregate_channels(
                processed_channels, strategy, context
            )

            # Log aggregation details
            if self.config.log_channel_processing:
                await self._log_aggregation(aggregated, context)

            # Store debug information
            if self.config.include_debug_info:
                await context.remember(
                    "multi_channel_debug",
                    {
                        "channels_parsed": len(channels),
                        "channels_processed": len(processed_channels),
                        "strategy_used": aggregated.strategy_applied.value,
                        "filters_applied": aggregated.filtering_applied,
                        "user_response_length": len(aggregated.user_response),
                        "debug_response_length": len(aggregated.debug_response),
                    },
                )

            return aggregated.user_response

        except Exception as e:
            # Log error and return original message
            await context.log(
                level="error",
                category="multi_channel_aggregator",
                message=f"Multi-channel aggregation error: {e!s}",
                error=str(e),
            )
            return context.message

    async def _parse_channels(self, message: str) -> list[ChannelContent]:
        """Parse multi-channel content from message.

        Args:
            message: Input message potentially containing multi-channel content

        Returns:
            List of parsed channel content
        """
        channels = []

        for channel_type, patterns in self._channel_patterns.items():
            # Skip disabled channels
            if not self._is_channel_enabled(channel_type):
                continue

            for pattern in patterns:
                matches = re.finditer(pattern, message, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    content = match.group(1).strip()
                    if content:  # Only add non-empty content
                        channel_content = ChannelContent(
                            channel_type=channel_type,
                            raw_content=content,
                            metadata={
                                "pattern_used": pattern,
                                "match_start": match.start(),
                                "match_end": match.end(),
                                "content_length": len(content),
                            },
                        )
                        channels.append(channel_content)
                        break  # Use first successful match per channel type

        return channels

    def _is_channel_enabled(self, channel_type: ChannelType) -> bool:
        """Check if a channel type is enabled in configuration."""
        channel_config_map = {
            ChannelType.ANALYSIS: self.config.enable_analysis_channel,
            ChannelType.COMMENTARY: self.config.enable_commentary_channel,
            ChannelType.FINAL: self.config.enable_final_channel,
        }
        return channel_config_map.get(channel_type, True)

    async def _determine_strategy(self, context) -> AggregationStrategy:
        """Determine aggregation strategy from context or configuration.

        Args:
            context: Plugin execution context

        Returns:
            Aggregation strategy to use
        """
        # Check for strategy override in context
        strategy_override = await context.recall(
            self.config.strategy_override_key, None
        )

        if strategy_override:
            try:
                return AggregationStrategy(strategy_override)
            except ValueError:
                pass  # Invalid strategy, use default

        try:
            return AggregationStrategy(self.config.default_strategy)
        except ValueError:
            return AggregationStrategy.USER_FRIENDLY

    async def _process_channel(
        self, channel: ChannelContent, context
    ) -> ChannelContent | None:
        """Process a single channel's content.

        Args:
            channel: Channel content to process
            context: Plugin execution context

        Returns:
            Processed channel content or None if filtered out
        """
        try:
            processed_content = channel.raw_content
            filters_applied = []

            # Apply safety filtering
            if self.config.enable_safety_filtering:
                processed_content, safety_filtered = await self._apply_safety_filter(
                    processed_content
                )
                if safety_filtered:
                    filters_applied.append("safety")

            # Apply technical jargon filtering for user-friendly content
            if self.config.filter_technical_jargon:
                (
                    processed_content,
                    jargon_filtered,
                ) = await self._filter_technical_jargon(processed_content)
                if jargon_filtered:
                    filters_applied.append("technical_jargon")

            # Calculate confidence score based on content quality indicators
            confidence = await self._calculate_channel_confidence(
                channel, processed_content
            )

            # Filter out low-confidence channels
            if confidence < self.config.min_channel_confidence:
                return None

            # Create processed channel
            processed_channel = ChannelContent(
                channel_type=channel.channel_type,
                raw_content=channel.raw_content,
                processed_content=processed_content,
                confidence_score=confidence,
                metadata={
                    **channel.metadata,
                    "filters_applied": filters_applied,
                    "processing_timestamp": (
                        context.timestamp if hasattr(context, "timestamp") else None
                    ),
                },
            )

            return processed_channel

        except Exception as e:
            await context.log(
                level="warning",
                category="channel_processing",
                message=f"Error processing {channel.channel_type.value} channel: {e!s}",
                channel_type=channel.channel_type.value,
                error=str(e),
            )
            return None

    async def _apply_safety_filter(self, content: str) -> tuple[str, bool]:
        """Apply safety filtering to content.

        Args:
            content: Content to filter

        Returns:
            Tuple of (filtered_content, was_filtered)
        """
        filtered = False

        for pattern in self._safety_patterns:
            if re.search(pattern, content):
                # Replace entire content with placeholder if harmful patterns found
                content = "[Content filtered for safety]"
                filtered = True
                break  # One replacement is enough

        return content, filtered

    async def _filter_technical_jargon(self, content: str) -> tuple[str, bool]:
        """Filter technical jargon from content.

        Args:
            content: Content to filter

        Returns:
            Tuple of (filtered_content, was_filtered)
        """
        if not self.config.filter_technical_jargon:
            return content, False

        original_length = len(content)

        for pattern in self._technical_patterns:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # Clean up extra whitespace
        content = re.sub(r"\s+", " ", content).strip()

        filtered = len(content) < original_length * 0.95  # 5% reduction threshold

        return content, filtered

    async def _calculate_channel_confidence(
        self, channel: ChannelContent, processed_content: str
    ) -> float:
        """Calculate confidence score for channel content.

        Args:
            channel: Original channel content
            processed_content: Processed content

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence - start lower for very short content
        if len(processed_content) < 10:
            confidence = 0.1  # Very low for very short content
        elif len(processed_content) < 30:
            confidence = 0.25  # Below threshold for short content
        else:
            confidence = 0.5

        # Content length indicators
        if len(processed_content) > 50:
            confidence += 0.2
        if len(processed_content) > 200:
            confidence += 0.1

        # Channel type weighting
        channel_weights = {
            ChannelType.FINAL: 0.3,  # Final responses are most important
            ChannelType.ANALYSIS: 0.2,  # Analysis provides good context
            ChannelType.COMMENTARY: 0.1,  # Commentary is supplementary
        }
        confidence += channel_weights.get(channel.channel_type, 0.0)

        # Quality indicators
        if any(
            word in processed_content.lower()
            for word in ["conclusion", "result", "answer", "solution"]
        ):
            confidence += 0.1

        # Reduce confidence for heavily filtered content
        if channel.raw_content and processed_content:
            reduction_ratio = len(processed_content) / len(channel.raw_content)
            if reduction_ratio < 0.5:  # More than 50% reduction
                confidence -= 0.2

        return max(0.0, min(1.0, confidence))

    async def _aggregate_channels(
        self, channels: list[ChannelContent], strategy: AggregationStrategy, context
    ) -> AggregatedResponse:
        """Aggregate multiple channels into a coherent response.

        Args:
            channels: Processed channel content
            strategy: Aggregation strategy to use
            context: Plugin execution context

        Returns:
            Aggregated response
        """
        if not channels:
            return AggregatedResponse(
                user_response="",
                debug_response="",
                channels_used=[],
                strategy_applied=strategy,
                filtering_applied=[],
                metadata={"error": "no_channels_to_aggregate"},
            )

        # Sort channels by priority and confidence
        sorted_channels = sorted(
            channels,
            key=lambda c: (
                self._get_channel_priority(c.channel_type),
                c.confidence_score or 0.0,
            ),
            reverse=True,
        )

        # Apply aggregation strategy
        if strategy == AggregationStrategy.USER_FRIENDLY:
            return await self._aggregate_user_friendly(sorted_channels, context)
        elif strategy == AggregationStrategy.DEBUGGING:
            return await self._aggregate_debugging(sorted_channels, context)
        elif strategy == AggregationStrategy.BALANCED:
            return await self._aggregate_balanced(sorted_channels, context)
        else:  # CUSTOM or fallback
            return await self._aggregate_custom(sorted_channels, context)

    def _get_channel_priority(self, channel_type: ChannelType) -> int:
        """Get priority for channel type (higher = more important)."""
        priority_map = {
            ChannelType.FINAL: 3,
            ChannelType.ANALYSIS: 2,
            ChannelType.COMMENTARY: 1,
        }
        return priority_map.get(channel_type, 0)

    async def _aggregate_user_friendly(
        self, channels: list[ChannelContent], context
    ) -> AggregatedResponse:
        """Aggregate channels for user-friendly output."""
        user_parts = []
        debug_parts = []
        filters_applied = set()

        # Prioritize final response, fallback to analysis
        primary_channel = None
        for channel in channels:
            if channel.channel_type == ChannelType.FINAL:
                primary_channel = channel
                break

        if not primary_channel and channels:
            primary_channel = channels[0]  # Use highest priority channel

        if primary_channel:
            user_parts.append(
                primary_channel.processed_content or primary_channel.raw_content
            )
            filters_applied.update(primary_channel.metadata.get("filters_applied", []))

        # Build debug response with all channels
        for channel in channels:
            prefix = self._get_channel_prefix(channel.channel_type)
            debug_parts.append(f"{prefix}\n{channel.raw_content}\n")

        user_response = " ".join(user_parts).strip()
        debug_response = "\n".join(debug_parts).strip()

        # Apply length limit
        if len(user_response) > self.config.max_user_response_length:
            user_response = (
                user_response[: self.config.max_user_response_length - 3] + "..."
            )
            filters_applied.add("length_limit")

        return AggregatedResponse(
            user_response=user_response,
            debug_response=debug_response,
            channels_used=[c.channel_type for c in channels],
            strategy_applied=AggregationStrategy.USER_FRIENDLY,
            filtering_applied=list(filters_applied),
            metadata={
                "primary_channel": (
                    primary_channel.channel_type.value if primary_channel else None
                ),
                "channels_count": len(channels),
            },
        )

    async def _aggregate_debugging(
        self, channels: list[ChannelContent], context
    ) -> AggregatedResponse:
        """Aggregate channels for debugging output (full context)."""
        debug_parts = []

        for channel in channels:
            prefix = self._get_channel_prefix(channel.channel_type)
            confidence = (
                f" (confidence: {channel.confidence_score:.2f})"
                if channel.confidence_score
                else ""
            )

            debug_parts.append(f"{prefix}{confidence}")
            debug_parts.append(f"Raw: {channel.raw_content}")
            if (
                channel.processed_content
                and channel.processed_content != channel.raw_content
            ):
                debug_parts.append(f"Processed: {channel.processed_content}")

            filters = channel.metadata.get("filters_applied", [])
            if filters:
                debug_parts.append(f"Filters: {', '.join(filters)}")

            debug_parts.append("")  # Empty line separator

        full_response = "\n".join(debug_parts).strip()

        return AggregatedResponse(
            user_response=full_response,  # Same as debug for debugging strategy
            debug_response=full_response,
            channels_used=[c.channel_type for c in channels],
            strategy_applied=AggregationStrategy.DEBUGGING,
            filtering_applied=[],  # No filtering in debug mode
            metadata={"full_debug_context": True},
        )

    async def _aggregate_balanced(
        self, channels: list[ChannelContent], context
    ) -> AggregatedResponse:
        """Aggregate channels for balanced output (mix of user-friendly and technical)."""
        user_parts = []
        filters_applied = set()

        # Start with user-friendly aggregation
        user_friendly = await self._aggregate_user_friendly(channels, context)
        user_parts.append(user_friendly.user_response)
        filters_applied.update(user_friendly.filtering_applied)

        # Add key technical insights from analysis channel
        analysis_channel = next(
            (c for c in channels if c.channel_type == ChannelType.ANALYSIS), None
        )

        if analysis_channel and analysis_channel.processed_content:
            # Extract key insights (sentences with high information density)
            insights = await self._extract_key_insights(
                analysis_channel.processed_content
            )
            if insights:
                user_parts.append(f"\nKey insights: {insights}")

        # Build full debug response
        debug_response = await self._aggregate_debugging(channels, context)

        return AggregatedResponse(
            user_response=" ".join(user_parts).strip(),
            debug_response=debug_response.debug_response,
            channels_used=[c.channel_type for c in channels],
            strategy_applied=AggregationStrategy.BALANCED,
            filtering_applied=list(filters_applied),
            metadata={"includes_key_insights": analysis_channel is not None},
        )

    async def _aggregate_custom(
        self, channels: list[ChannelContent], context
    ) -> AggregatedResponse:
        """Aggregate channels using custom strategy (fallback to balanced)."""
        # For now, use balanced strategy as custom fallback
        balanced = await self._aggregate_balanced(channels, context)
        balanced.strategy_applied = AggregationStrategy.CUSTOM
        return balanced

    async def _extract_key_insights(self, content: str) -> str:
        """Extract key insights from analysis content."""
        sentences = re.split(r"[.!?]+", content)

        # Look for sentences with insight indicators
        insight_indicators = [
            "important",
            "key",
            "critical",
            "significant",
            "note that",
            "however",
            "therefore",
            "consequently",
            "indicates",
            "suggests",
        ]

        insights = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(
                indicator in sentence.lower() for indicator in insight_indicators
            ):
                insights.append(sentence)

        return ". ".join(insights[:2])  # Limit to 2 key insights

    def _get_channel_prefix(self, channel_type: ChannelType) -> str:
        """Get display prefix for channel type."""
        prefix_map = {
            ChannelType.ANALYSIS: self.config.analysis_prefix,
            ChannelType.COMMENTARY: self.config.commentary_prefix,
            ChannelType.FINAL: self.config.final_prefix,
        }
        return prefix_map.get(channel_type, f"[{channel_type.value.title()}]")

    async def _log_aggregation(self, aggregated: AggregatedResponse, context) -> None:
        """Log aggregation details for monitoring."""
        await context.log(
            level="info",
            category="multi_channel_aggregator",
            message="Multi-channel aggregation completed",
            strategy=aggregated.strategy_applied.value,
            channels_used=[c.value for c in aggregated.channels_used],
            filters_applied=aggregated.filtering_applied,
            user_response_length=len(aggregated.user_response),
            debug_response_length=len(aggregated.debug_response),
            metadata=aggregated.metadata,
        )

    # Public API methods

    async def set_aggregation_strategy(
        self, strategy: AggregationStrategy, context
    ) -> None:
        """Set aggregation strategy for current context.

        Args:
            strategy: Aggregation strategy to use
            context: Plugin execution context
        """
        await context.remember(self.config.strategy_override_key, strategy.value)

    async def get_channel_stats(self) -> dict[str, Any]:
        """Get statistics about channel processing."""
        return {
            "supported_channels": [c.value for c in ChannelType],
            "enabled_channels": [
                c.value for c in ChannelType if self._is_channel_enabled(c)
            ],
            "available_strategies": [s.value for s in AggregationStrategy],
            "default_strategy": self.config.default_strategy,
            "safety_filtering_enabled": self.config.enable_safety_filtering,
            "technical_filtering_enabled": self.config.filter_technical_jargon,
        }

    async def process_multi_channel_content(
        self, content: str, strategy: AggregationStrategy | None = None
    ) -> AggregatedResponse:
        """Process multi-channel content programmatically.

        Args:
            content: Multi-channel content to process
            strategy: Optional strategy override

        Returns:
            Aggregated response
        """

        # Create minimal context for processing
        class MockContext:
            def __init__(self):
                self.message = content
                self.timestamp = None

            async def log(self, **kwargs):
                pass

            async def remember(self, key, value):
                pass

            async def recall(self, key, default=None):
                if (
                    key == "aggregation_strategy" and strategy
                ):  # Use the actual config value
                    return strategy.value
                return default

        mock_context = MockContext()

        # Parse and process channels
        channels = await self._parse_channels(content)
        processed_channels = []

        for channel in channels:
            processed = await self._process_channel(channel, mock_context)
            if processed:
                processed_channels.append(processed)

        # Aggregate
        used_strategy = strategy or self.config.default_strategy
        return await self._aggregate_channels(
            processed_channels, used_strategy, mock_context
        )
