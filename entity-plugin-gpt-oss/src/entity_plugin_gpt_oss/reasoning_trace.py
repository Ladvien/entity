"""Reasoning Trace Plugin for capturing and analyzing GPT-OSS chain-of-thought.

This plugin extracts and stores raw chain-of-thought reasoning from the analysis
channel of GPT-OSS responses, making it available for debugging, auditing, and
improvement of agent decision-making.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from entity.plugins.prompt import PromptPlugin
from entity.workflow.executor import WorkflowExecutor
from pydantic import BaseModel, Field


class ReasoningLevel(Enum):
    """Reasoning effort levels for task complexity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReasoningTrace(BaseModel):
    """Model for a reasoning trace record."""

    execution_id: str = Field(description="Unique ID for this execution")
    timestamp: str = Field(description="ISO format timestamp")
    level: str = Field(description="Reasoning level used")  # Store as string
    task: str = Field(description="Original task/message")
    analysis: str = Field(description="Raw analysis channel content")
    commentary: str | None = Field(
        default=None, description="Commentary channel if present"
    )
    filtered_content: list[str] = Field(
        default_factory=list, description="Content filtered for safety"
    )
    complexity_score: float = Field(description="Computed complexity score (0-1)")
    tokens_used: int | None = Field(
        default=None, description="Tokens used in reasoning"
    )


class ReasoningTracePlugin(PromptPlugin):
    """Plugin that captures and stores GPT-OSS chain-of-thought reasoning.

    This plugin runs in the THINK stage of Entity's pipeline and:
    - Extracts raw CoT from the analysis channel
    - Stores reasoning traces in Entity's memory system
    - Filters potentially harmful content before storage
    - Provides configurable reasoning levels based on task complexity
    - Maintains a queryable history of reasoning patterns
    """

    supported_stages = [WorkflowExecutor.THINK]
    dependencies = ["llm", "memory"]

    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        """Initialize the plugin and validate configuration."""
        super().__init__(resources, config)
        # Validate and set config as model instance
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.error}")

    class ConfigModel(BaseModel):
        """Configuration for the reasoning trace plugin."""

        default_level: ReasoningLevel = Field(
            default=ReasoningLevel.MEDIUM,
            description="Default reasoning level if not determined dynamically",
        )
        enable_filtering: bool = Field(
            default=True, description="Enable harmful content filtering"
        )
        store_commentary: bool = Field(
            default=True, description="Also store commentary channel if present"
        )
        complexity_threshold_high: float = Field(
            default=0.8, description="Complexity score threshold for HIGH reasoning"
        )
        complexity_threshold_medium: float = Field(
            default=0.4, description="Complexity score threshold for MEDIUM reasoning"
        )
        max_trace_length: int = Field(
            default=10000, description="Maximum characters to store per trace"
        )
        harmful_patterns: list[str] = Field(
            default_factory=lambda: [
                r"(?i)(exploit|attack|hack|malicious)",
                r"(?i)(kill|harm|hurt|destroy)",
                r"(?i)(illegal|criminal|illicit)",
            ],
            description="Regex patterns for harmful content to filter",
        )

        class Config:
            use_enum_values = True

    async def _execute_impl(self, context) -> str:
        """Execute the reasoning trace plugin."""
        # Generate unique execution ID
        execution_id = str(uuid.uuid4())

        # Get the current message/task
        task = context.message or ""

        # Determine reasoning level based on task complexity
        reasoning_level = await self._determine_reasoning_level(context, task)

        # Check if we have harmony infrastructure with channels
        llm = context.get_resource("llm")
        if hasattr(llm, "infrastructure") and hasattr(
            llm.infrastructure, "generate_with_channels"
        ):
            # Get multi-channel response
            channels = await llm.infrastructure.generate_with_channels(task)
            analysis_content = channels.get("analysis", "")
            commentary_content = (
                channels.get("commentary", "") if self.config.store_commentary else None
            )
        else:
            # Fallback: extract from regular response
            response = await llm.generate(task)
            analysis_content = await self._extract_analysis_channel(response)
            commentary_content = None

        # Filter harmful content if enabled
        filtered_content = []
        if self.config.enable_filtering:
            analysis_content, filtered = await self._filter_harmful_content(
                analysis_content
            )
            filtered_content = filtered

        # Calculate complexity score
        complexity_score = await self._calculate_complexity(task)

        # Create reasoning trace record
        trace = ReasoningTrace(
            execution_id=execution_id,
            timestamp=datetime.now().isoformat(),
            level=(
                reasoning_level.value
                if isinstance(reasoning_level, ReasoningLevel)
                else reasoning_level
            ),
            task=task[:500],  # Truncate task for storage
            analysis=analysis_content[: self.config.max_trace_length],
            commentary=(
                commentary_content[: self.config.max_trace_length]
                if commentary_content
                else None
            ),
            filtered_content=filtered_content,
            complexity_score=complexity_score,
            tokens_used=len(analysis_content.split()),  # Simple approximation
        )

        # Store reasoning trace in memory
        await context.remember(f"reasoning_trace:{execution_id}", trace.model_dump())

        # Update reasoning history index
        history = await context.recall("reasoning_history", [])
        history.append(
            {
                "execution_id": execution_id,
                "timestamp": trace.timestamp,
                "task_preview": task[:100],
                "level": reasoning_level.value,
                "complexity": complexity_score,
            }
        )
        # Keep only last 100 entries in index
        if len(history) > 100:
            history = history[-100:]
        await context.remember("reasoning_history", history)

        # Store reasoning level for other plugins to use
        await context.remember(f"reasoning_level:{execution_id}", reasoning_level.value)

        # Pass through the message unchanged
        return context.message

    async def _determine_reasoning_level(self, context, task: str) -> ReasoningLevel:
        """Determine appropriate reasoning level based on task complexity."""
        complexity_score = await self._calculate_complexity(task)

        # Check for manual override in context
        manual_level = await context.recall("reasoning_level_override")
        if manual_level:
            try:
                return ReasoningLevel(manual_level)
            except ValueError:
                pass

        # Determine based on complexity
        if complexity_score >= self.config.complexity_threshold_high:
            return ReasoningLevel.HIGH
        elif complexity_score >= self.config.complexity_threshold_medium:
            return ReasoningLevel.MEDIUM
        else:
            return ReasoningLevel.LOW

    async def _calculate_complexity(self, task: str) -> float:
        """Calculate task complexity score (0-1)."""
        # Simple heuristic-based complexity scoring
        score = 0.0

        # Length factor
        word_count = len(task.split())
        if word_count > 100:
            score += 0.3
        elif word_count > 50:
            score += 0.2
        elif word_count > 20:
            score += 0.1

        # Question complexity
        question_words = ["why", "how", "explain", "analyze", "compare", "evaluate"]
        for word in question_words:
            if word.lower() in task.lower():
                score += 0.15

        # Technical terms
        technical_patterns = [
            r"\b(algorithm|optimize|implement|architecture|framework)\b",
            r"\b(async|concurrent|parallel|distributed)\b",
            r"\b(machine learning|neural|AI|model)\b",
        ]
        for pattern in technical_patterns:
            if re.search(pattern, task, re.IGNORECASE):
                score += 0.1

        # Multi-step indicators
        if any(word in task.lower() for word in ["then", "after", "next", "finally"]):
            score += 0.2

        # Code blocks
        if "```" in task or "def " in task or "class " in task:
            score += 0.2

        return min(score, 1.0)

    async def _extract_analysis_channel(self, response: str) -> str:
        """Extract analysis channel content from a response."""
        # Look for analysis channel markers
        if "<<ANALYSIS>>" in response:
            lines = response.split("\n")
            analysis_lines = []
            in_analysis = False

            for line in lines:
                if "<<ANALYSIS>>" in line:
                    in_analysis = True
                    continue
                elif "<<COMMENTARY>>" in line or "<<FINAL>>" in line:
                    in_analysis = False
                elif in_analysis:
                    analysis_lines.append(line)

            return "\n".join(analysis_lines).strip()

        # Fallback: look for thinking patterns
        thinking_patterns = [
            r"(?i)(I need to|Let me think|First,? I|Consider)",
            r"(?i)(The problem is|This means|Therefore|Because)",
            r"(?i)(Step \d+|Option \d+|Approach \d+)",
        ]

        analysis_parts = []
        for line in response.split("\n"):
            for pattern in thinking_patterns:
                if re.search(pattern, line):
                    analysis_parts.append(line)
                    break

        return "\n".join(analysis_parts) if analysis_parts else ""

    async def _filter_harmful_content(self, content: str) -> tuple[str, list[str]]:
        """Filter potentially harmful content from reasoning traces."""
        filtered_lines = []
        clean_lines = []

        for line in content.split("\n"):
            is_harmful = False
            for pattern in self.config.harmful_patterns:
                if re.search(pattern, line):
                    is_harmful = True
                    filtered_lines.append(line[:50] + "... [FILTERED]")
                    break

            if not is_harmful:
                clean_lines.append(line)

        return "\n".join(clean_lines), filtered_lines

    @classmethod
    async def retrieve_reasoning_history(
        cls,
        context,
        limit: int = 10,
        min_complexity: float | None = None,
        level: ReasoningLevel | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve historical reasoning traces based on filters.

        Args:
            context: Plugin context with memory access
            limit: Maximum number of traces to return
            min_complexity: Minimum complexity score filter
            level: Filter by specific reasoning level

        Returns:
            List of reasoning trace summaries
        """
        history = await context.recall("reasoning_history", [])

        # Apply filters
        filtered = history
        if min_complexity is not None:
            filtered = [h for h in filtered if h.get("complexity", 0) >= min_complexity]
        if level is not None:
            filtered = [h for h in filtered if h.get("level") == level.value]

        # Sort by timestamp (most recent first)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply limit
        return filtered[:limit]

    @classmethod
    async def get_reasoning_trace(
        cls, context, execution_id: str
    ) -> ReasoningTrace | None:
        """Retrieve a specific reasoning trace by execution ID.

        Args:
            context: Plugin context with memory access
            execution_id: Unique execution ID

        Returns:
            ReasoningTrace object or None if not found
        """
        trace_data = await context.recall(f"reasoning_trace:{execution_id}")
        if trace_data:
            return ReasoningTrace(**trace_data)
        return None

    @classmethod
    async def analyze_reasoning_patterns(
        cls, context, time_window_hours: int = 24
    ) -> dict[str, Any]:
        """Analyze reasoning patterns over a time window.

        Args:
            context: Plugin context with memory access
            time_window_hours: Hours to look back for analysis

        Returns:
            Dictionary with pattern analysis metrics
        """
        history = await context.recall("reasoning_history", [])

        # Filter by time window
        # Note: In production, properly parse and compare timestamps
        recent = history[-50:] if len(history) > 50 else history

        # Calculate metrics
        if not recent:
            return {
                "total_traces": 0,
                "avg_complexity": 0,
                "level_distribution": {},
                "high_complexity_tasks": [],
            }

        complexities = [h.get("complexity", 0) for h in recent]
        levels = [h.get("level", "medium") for h in recent]

        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1

        high_complexity = [h for h in recent if h.get("complexity", 0) >= 0.8]

        return {
            "total_traces": len(recent),
            "avg_complexity": (
                sum(complexities) / len(complexities) if complexities else 0
            ),
            "level_distribution": level_counts,
            "high_complexity_tasks": high_complexity[:5],
        }
