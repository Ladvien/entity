"""Reasoning Analytics Dashboard Plugin for GPT-OSS.

This plugin collects, aggregates, and provides visualization APIs for reasoning
trace data from gpt-oss interactions. It enables product managers to analyze
reasoning patterns, identify bottlenecks, and optimize agent performance.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin


class ReasoningMetrics(BaseModel):
    """Model for reasoning execution metrics."""

    execution_id: str = Field(description="Unique execution identifier")
    timestamp: datetime = Field(description="Execution timestamp")
    reasoning_depth: int = Field(description="Number of reasoning steps")
    complexity_score: float = Field(description="Complexity score 0-1")
    duration_ms: int = Field(description="Execution duration in milliseconds")
    token_count: int = Field(description="Total tokens used")
    reasoning_level: str = Field(description="Reasoning level (low/medium/high)")
    task_category: str = Field(description="Category of the task")
    success: bool = Field(description="Whether execution was successful")
    error_type: Optional[str] = Field(default=None, description="Error type if failed")


class PatternAnalysis(BaseModel):
    """Model for aggregated pattern analysis."""

    pattern_type: str = Field(description="Type of pattern identified")
    frequency: int = Field(description="How often this pattern occurs")
    avg_complexity: float = Field(description="Average complexity for this pattern")
    avg_duration_ms: int = Field(description="Average duration in milliseconds")
    success_rate: float = Field(description="Success rate for this pattern")


class BottleneckAnalysis(BaseModel):
    """Model for identified bottlenecks."""

    bottleneck_type: str = Field(description="Type of bottleneck")
    severity: str = Field(description="Severity level (low/medium/high)")
    affected_tasks: List[str] = Field(description="Task categories affected")
    impact_score: float = Field(description="Impact score 0-1")
    suggested_optimization: str = Field(description="Optimization suggestion")


class DashboardData(BaseModel):
    """Model for dashboard visualization data."""

    total_executions: int = Field(description="Total number of executions")
    avg_complexity: float = Field(description="Average complexity score")
    avg_duration_ms: int = Field(description="Average execution duration")
    success_rate: float = Field(description="Overall success rate")
    patterns: List[PatternAnalysis] = Field(description="Identified patterns")
    bottlenecks: List[BottleneckAnalysis] = Field(description="Identified bottlenecks")
    time_series: Dict[str, List[float]] = Field(description="Time series data")


class ReasoningAnalyticsDashboardPlugin(Plugin):
    """Analytics dashboard plugin for reasoning trace data."""

    class ConfigModel(BaseModel):
        """Configuration for reasoning analytics dashboard."""

        max_stored_metrics: int = Field(
            default=10000, description="Maximum number of metrics to store in memory"
        )
        analysis_window_hours: int = Field(
            default=24, description="Time window for analysis in hours"
        )
        complexity_threshold: float = Field(
            default=0.7, description="Complexity threshold for bottleneck detection"
        )
        duration_threshold_ms: int = Field(
            default=5000,
            description="Duration threshold in ms for bottleneck detection",
        )
        enable_real_time_monitoring: bool = Field(
            default=True, description="Enable real-time monitoring capabilities"
        )

        class Config:
            extra = "forbid"

    supported_stages = ["analysis", "post_processing"]
    dependencies = []

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the reasoning analytics dashboard plugin."""
        super().__init__(resources, config)

        # Validate and convert config to model
        result = self.validate_config()
        if not result.success:
            raise ValueError(f"Invalid config: {', '.join(result.errors)}")

        # In-memory storage for metrics (in production, use persistent storage)
        self._metrics_store: List[ReasoningMetrics] = []
        self._patterns_cache: Optional[List[PatternAnalysis]] = None
        self._bottlenecks_cache: Optional[List[BottleneckAnalysis]] = None
        self._last_analysis_time: Optional[datetime] = None

    async def _execute_impl(self, context: Any) -> Any:
        """Execute reasoning analytics collection and analysis."""
        # Extract reasoning data from context
        metrics = await self._extract_reasoning_metrics(context)

        if metrics:
            # Store metrics
            self._store_metrics(metrics)

            # Trigger analysis if needed
            if self._should_run_analysis():
                await self._run_pattern_analysis()
                await self._run_bottleneck_detection()
                self._last_analysis_time = datetime.now()

        # Add analytics metadata to context
        context.reasoning_analytics = {
            "metrics_collected": bool(metrics),
            "total_stored_metrics": len(self._metrics_store),
            "last_analysis": (
                self._last_analysis_time.isoformat()
                if self._last_analysis_time
                else None
            ),
        }

        return context

    async def _extract_reasoning_metrics(
        self, context: Any
    ) -> Optional[ReasoningMetrics]:
        """Extract reasoning metrics from execution context."""
        try:
            # Get execution metadata
            execution_id = getattr(
                context, "execution_id", f"exec_{datetime.now().timestamp()}"
            )

            # Extract reasoning trace data if available
            reasoning_trace = getattr(context, "reasoning_trace", None)
            if not reasoning_trace:
                return None

            # Calculate metrics
            reasoning_depth = self._calculate_reasoning_depth(reasoning_trace)
            complexity_score = self._calculate_complexity_score(reasoning_trace)
            duration_ms = getattr(context, "execution_duration_ms", 0)
            token_count = getattr(context, "token_count", 0)
            reasoning_level = getattr(context, "reasoning_level", "medium")
            task_category = self._categorize_task(getattr(context, "task", ""))
            success = getattr(context, "execution_success", True)
            error_type = getattr(context, "error_type", None) if not success else None

            return ReasoningMetrics(
                execution_id=execution_id,
                timestamp=datetime.now(),
                reasoning_depth=reasoning_depth,
                complexity_score=complexity_score,
                duration_ms=duration_ms,
                token_count=token_count,
                reasoning_level=reasoning_level,
                task_category=task_category,
                success=success,
                error_type=error_type,
            )

        except Exception as e:
            # Log error but don't fail the main execution
            print(f"Warning: Could not extract reasoning metrics: {e}")
            return None

    def _calculate_reasoning_depth(self, reasoning_trace: Any) -> int:
        """Calculate the depth of reasoning steps."""
        if isinstance(reasoning_trace, dict):
            analysis = reasoning_trace.get("analysis", "")
        elif hasattr(reasoning_trace, "analysis"):
            analysis = reasoning_trace.analysis
        else:
            analysis = str(reasoning_trace)

        # Simple heuristic: count reasoning indicators
        reasoning_indicators = [
            "therefore",
            "because",
            "since",
            "given that",
            "considering",
            "step ",
            "first",
            "second",
            "third",
            "next",
            "then",
            "if ",
            "when ",
            "unless",
            "provided that",
        ]

        depth = sum(
            analysis.lower().count(indicator) for indicator in reasoning_indicators
        )
        return max(1, depth)  # Minimum depth of 1

    def _calculate_complexity_score(self, reasoning_trace: Any) -> float:
        """Calculate complexity score based on reasoning content."""
        if isinstance(reasoning_trace, dict):
            analysis = reasoning_trace.get("analysis", "")
        elif hasattr(reasoning_trace, "analysis"):
            analysis = reasoning_trace.analysis
        else:
            analysis = str(reasoning_trace)

        # Factors that increase complexity
        complexity_factors = {
            "conditional": len(
                [
                    w
                    for w in analysis.lower().split()
                    if w in ["if", "unless", "when", "provided"]
                ]
            ),
            "comparisons": analysis.lower().count("compared to")
            + analysis.lower().count("versus"),
            "abstractions": analysis.lower().count("concept")
            + analysis.lower().count("abstract"),
            "length": min(len(analysis.split()) / 200, 1.0),  # Normalize by word count
            "technical_terms": len(
                [w for w in analysis.lower().split() if len(w) > 8]
            ),  # Long technical words
        }

        # Calculate weighted complexity score
        weights = {
            "conditional": 0.3,
            "comparisons": 0.2,
            "abstractions": 0.2,
            "length": 0.2,
            "technical_terms": 0.1,
        }
        score = sum(
            complexity_factors[factor] * weights[factor]
            for factor in complexity_factors
        )

        return min(score, 1.0)  # Cap at 1.0

    def _categorize_task(self, task: str) -> str:
        """Categorize the task type for analysis."""
        task_lower = task.lower()

        # Check in order of specificity
        if any(
            word in task_lower
            for word in ["explain", "describe", "define", "what does"]
        ):
            return "explanation"
        elif any(
            word in task_lower for word in ["code", "program", "function", "debug"]
        ):
            return "coding"
        elif any(
            word in task_lower for word in ["analyze", "data", "statistics", "metrics"]
        ):
            return "analysis"
        elif any(
            word in task_lower for word in ["write", "compose", "draft", "document"]
        ):
            return "writing"
        elif any(
            word in task_lower for word in ["solve", "calculate", "math", "problem"]
        ):
            return "problem_solving"
        else:
            return "general"

    def _store_metrics(self, metrics: ReasoningMetrics) -> None:
        """Store metrics with size management."""
        self._metrics_store.append(metrics)

        # Trim old metrics if we exceed the limit
        max_stored = self.config.max_stored_metrics
        if len(self._metrics_store) > max_stored:
            # Keep the most recent metrics
            self._metrics_store = self._metrics_store[-max_stored:]

        # Invalidate caches
        self._patterns_cache = None
        self._bottlenecks_cache = None

    def _should_run_analysis(self) -> bool:
        """Determine if we should run pattern analysis."""
        if not self._last_analysis_time:
            return True

        # Run analysis every hour or when we have significant new data
        time_threshold = datetime.now() - timedelta(hours=1)
        return self._last_analysis_time < time_threshold

    async def _run_pattern_analysis(self) -> None:
        """Analyze patterns in reasoning data."""
        if not self._metrics_store:
            return

        # Group by task category and reasoning level
        patterns = defaultdict(list)

        for metric in self._metrics_store:
            key = f"{metric.task_category}_{metric.reasoning_level}"
            patterns[key].append(metric)

        pattern_analyses = []
        for pattern_type, metrics_list in patterns.items():
            if len(metrics_list) < 3:  # Need minimum data for pattern
                continue

            avg_complexity = statistics.mean(m.complexity_score for m in metrics_list)
            avg_duration = statistics.mean(m.duration_ms for m in metrics_list)
            success_rate = sum(1 for m in metrics_list if m.success) / len(metrics_list)

            pattern_analyses.append(
                PatternAnalysis(
                    pattern_type=pattern_type,
                    frequency=len(metrics_list),
                    avg_complexity=avg_complexity,
                    avg_duration_ms=int(avg_duration),
                    success_rate=success_rate,
                )
            )

        self._patterns_cache = pattern_analyses

    async def _run_bottleneck_detection(self) -> None:
        """Detect reasoning bottlenecks."""
        if not self._metrics_store:
            return

        bottlenecks = []

        # High complexity bottleneck
        high_complexity_metrics = [
            m
            for m in self._metrics_store
            if m.complexity_score > self.config.complexity_threshold
        ]

        if high_complexity_metrics:
            affected_tasks = list(set(m.task_category for m in high_complexity_metrics))
            impact_score = len(high_complexity_metrics) / len(self._metrics_store)

            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="high_complexity",
                    severity="medium" if impact_score < 0.3 else "high",
                    affected_tasks=affected_tasks,
                    impact_score=impact_score,
                    suggested_optimization="Consider breaking down complex tasks into simpler components",
                )
            )

        # Long duration bottleneck
        slow_metrics = [
            m
            for m in self._metrics_store
            if m.duration_ms > self.config.duration_threshold_ms
        ]

        if slow_metrics:
            affected_tasks = list(set(m.task_category for m in slow_metrics))
            impact_score = len(slow_metrics) / len(self._metrics_store)

            bottlenecks.append(
                BottleneckAnalysis(
                    bottleneck_type="long_duration",
                    severity="low" if impact_score < 0.2 else "medium",
                    affected_tasks=affected_tasks,
                    impact_score=impact_score,
                    suggested_optimization="Optimize reasoning algorithms or increase timeout thresholds",
                )
            )

        # Low success rate bottleneck
        failed_metrics = [m for m in self._metrics_store if not m.success]
        if failed_metrics:
            failure_rate = len(failed_metrics) / len(self._metrics_store)
            if failure_rate > 0.1:  # More than 10% failure rate
                affected_tasks = list(set(m.task_category for m in failed_metrics))

                bottlenecks.append(
                    BottleneckAnalysis(
                        bottleneck_type="high_failure_rate",
                        severity="high" if failure_rate > 0.25 else "medium",
                        affected_tasks=affected_tasks,
                        impact_score=failure_rate,
                        suggested_optimization="Review error patterns and improve error handling",
                    )
                )

        self._bottlenecks_cache = bottlenecks

    def get_dashboard_data(
        self, time_window_hours: Optional[int] = None
    ) -> DashboardData:
        """Get aggregated dashboard data for visualization."""
        window_hours = time_window_hours or self.config.analysis_window_hours
        cutoff_time = datetime.now() - timedelta(hours=window_hours)

        # Filter metrics by time window
        recent_metrics = [m for m in self._metrics_store if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return DashboardData(
                total_executions=0,
                avg_complexity=0.0,
                avg_duration_ms=0,
                success_rate=0.0,
                patterns=[],
                bottlenecks=[],
                time_series={},
            )

        # Calculate summary statistics
        total_executions = len(recent_metrics)
        avg_complexity = statistics.mean(m.complexity_score for m in recent_metrics)
        avg_duration_ms = int(statistics.mean(m.duration_ms for m in recent_metrics))
        success_rate = sum(1 for m in recent_metrics if m.success) / total_executions

        # Generate time series data (hourly buckets)
        time_series = self._generate_time_series(recent_metrics, window_hours)

        return DashboardData(
            total_executions=total_executions,
            avg_complexity=avg_complexity,
            avg_duration_ms=avg_duration_ms,
            success_rate=success_rate,
            patterns=self._patterns_cache or [],
            bottlenecks=self._bottlenecks_cache or [],
            time_series=time_series,
        )

    def _generate_time_series(
        self, metrics: List[ReasoningMetrics], window_hours: int
    ) -> Dict[str, List[float]]:
        """Generate time series data for visualization."""
        # Create hourly buckets
        buckets = defaultdict(list)
        now = datetime.now()

        for metric in metrics:
            # Calculate hours ago (0 = current hour, 1 = last hour, etc.)
            hours_ago = int((now - metric.timestamp).total_seconds() / 3600)
            if hours_ago < window_hours:
                buckets[hours_ago].append(metric)

        # Generate time series arrays
        time_series = {
            "complexity": [],
            "duration": [],
            "success_rate": [],
            "throughput": [],
        }

        for hour in range(window_hours):
            hour_metrics = buckets.get(hour, [])

            if hour_metrics:
                time_series["complexity"].append(
                    statistics.mean(m.complexity_score for m in hour_metrics)
                )
                time_series["duration"].append(
                    statistics.mean(m.duration_ms for m in hour_metrics)
                )
                time_series["success_rate"].append(
                    sum(1 for m in hour_metrics if m.success) / len(hour_metrics)
                )
                time_series["throughput"].append(len(hour_metrics))
            else:
                # Fill with zeros for hours with no data
                time_series["complexity"].append(0.0)
                time_series["duration"].append(0.0)
                time_series["success_rate"].append(0.0)
                time_series["throughput"].append(0)

        return time_series

    def export_data(
        self, format_type: str = "json", time_window_hours: Optional[int] = None
    ) -> str:
        """Export analytics data for external analysis."""
        dashboard_data = self.get_dashboard_data(time_window_hours)

        if format_type == "json":
            return dashboard_data.model_dump_json(indent=2)
        elif format_type == "csv":
            # Convert to CSV format (simplified)
            lines = [
                "execution_id,timestamp,complexity,duration_ms,success,task_category"
            ]

            window_hours = time_window_hours or self.config.analysis_window_hours
            cutoff_time = datetime.now() - timedelta(hours=window_hours)

            for metric in self._metrics_store:
                if metric.timestamp >= cutoff_time:
                    lines.append(
                        f"{metric.execution_id},{metric.timestamp.isoformat()},"
                        f"{metric.complexity_score},{metric.duration_ms},"
                        f"{metric.success},{metric.task_category}"
                    )

            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time monitoring status."""
        if not self.config.enable_real_time_monitoring:
            return {"status": "disabled"}

        recent_metrics = [
            m
            for m in self._metrics_store
            if (datetime.now() - m.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        return {
            "status": "active",
            "recent_executions": len(recent_metrics),
            "avg_recent_complexity": (
                statistics.mean(m.complexity_score for m in recent_metrics)
                if recent_metrics
                else 0
            ),
            "recent_success_rate": (
                sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
                if recent_metrics
                else 1.0
            ),
            "active_bottlenecks": (
                len(self._bottlenecks_cache) if self._bottlenecks_cache else 0
            ),
            "last_update": datetime.now().isoformat(),
        }
