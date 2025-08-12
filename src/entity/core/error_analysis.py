"""Error analysis and debugging utilities for Entity Framework.

This module provides tools for analyzing error patterns, suggesting recovery
strategies, and debugging pipeline issues.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from entity.core.errors import ErrorCategory, PipelineError


@dataclass
class ErrorPattern:
    """Represents a detected error pattern."""

    signature: str
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    error_category: ErrorCategory
    affected_stages: Set[str]
    affected_plugins: Set[str]
    common_contexts: Dict[str, Any]
    suggested_fixes: List[str]


@dataclass
class RecoveryStrategy:
    """Represents an error recovery strategy."""

    name: str
    description: str
    applicable_categories: Set[ErrorCategory]
    success_rate: float
    implementation_notes: str
    code_example: Optional[str] = None


class ErrorAnalyzer:
    """Analyzes error patterns and suggests recovery strategies."""

    def __init__(self):
        self.error_history: List[PipelineError] = []
        self.patterns: Dict[str, ErrorPattern] = {}
        self.recovery_strategies = self._init_recovery_strategies()
        self.pattern_threshold = 3

    def _init_recovery_strategies(self) -> List[RecoveryStrategy]:
        """Initialize built-in recovery strategies."""
        return [
            RecoveryStrategy(
                name="retry_with_backoff",
                description="Retry operation with exponential backoff",
                applicable_categories={ErrorCategory.NETWORK, ErrorCategory.TIMEOUT},
                success_rate=0.7,
                implementation_notes="Use exponential backoff starting at 1s, max 30s",
                code_example="""
async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
""",
            ),
            RecoveryStrategy(
                name="fallback_plugin",
                description="Use alternative plugin when primary fails",
                applicable_categories={ErrorCategory.PLUGIN},
                success_rate=0.8,
                implementation_notes="Configure fallback plugins for critical stages",
                code_example="""
# In workflow configuration
fallback_plugins = {
    'primary_plugin': 'fallback_plugin',
    'ml_processor': 'simple_processor'
}
""",
            ),
            RecoveryStrategy(
                name="input_sanitization",
                description="Sanitize and validate input before processing",
                applicable_categories={ErrorCategory.VALIDATION, ErrorCategory.SANDBOX},
                success_rate=0.9,
                implementation_notes="Add input validation at pipeline entry points",
                code_example="""
def sanitize_input(data):
    # Remove dangerous patterns
    data = re.sub(r'[<>"\';\\]', '', data)
    # Validate length
    return data[:1000] if len(data) > 1000 else data
""",
            ),
            RecoveryStrategy(
                name="resource_cleanup",
                description="Clean up resources and retry operation",
                applicable_categories={ErrorCategory.RESOURCE, ErrorCategory.MEMORY},
                success_rate=0.6,
                implementation_notes="Trigger garbage collection and resource cleanup",
                code_example="""
async def cleanup_and_retry(operation):
    try:
        return await operation()
    except ResourceError:
        # Cleanup resources
        gc.collect()
        await cleanup_temp_files()
        # Retry once
        return await operation()
""",
            ),
            RecoveryStrategy(
                name="safe_mode_execution",
                description="Execute in restricted safe mode",
                applicable_categories={ErrorCategory.SANDBOX, ErrorCategory.PLUGIN},
                success_rate=0.5,
                implementation_notes="Disable advanced features and use minimal execution",
                code_example="""
# Enable safe mode
context.safe_mode = True
context.disable_features = ['file_access', 'network', 'subprocess']
""",
            ),
        ]

    def record_error(self, error: PipelineError) -> None:
        """Record an error for pattern analysis."""
        self.error_history.append(error)

        signature = self._generate_error_signature(error)
        if signature in self.patterns:
            pattern = self.patterns[signature]
            pattern.occurrences += 1
            pattern.last_seen = error.context.timestamp
            pattern.affected_stages.add(error.stage)
            if error.plugin:
                pattern.affected_plugins.add(error.plugin)
            self._update_common_contexts(pattern, error)
        else:
            self.patterns[signature] = ErrorPattern(
                signature=signature,
                occurrences=1,
                first_seen=error.context.timestamp,
                last_seen=error.context.timestamp,
                error_category=error.category,
                affected_stages={error.stage},
                affected_plugins={error.plugin} if error.plugin else set(),
                common_contexts=error.context.execution_context.copy(),
                suggested_fixes=[],
            )

        pattern = self.patterns[signature]
        if pattern.occurrences >= self.pattern_threshold:
            pattern.suggested_fixes = self._generate_fix_suggestions(pattern)

    def _generate_error_signature(self, error: PipelineError) -> str:
        """Generate a signature for error pattern matching."""
        error_type = error.original_error.__class__.__name__
        category = error.category.value

        message = str(error.original_error).lower()
        key_words = []

        patterns = [
            r"(\w+error)\b",
            r"(timeout)\b",
            r"(connection)\b",
            r"(permission)\b",
            r"(not found)\b",
            r"(invalid)\b",
            r"(failed)\b",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message)
            key_words.extend(matches)

        stage_part = f":{error.stage}" if error.stage else ""

        return f"{category}:{error_type}:{'-'.join(sorted(set(key_words)))}{stage_part}"

    def _update_common_contexts(
        self, pattern: ErrorPattern, error: PipelineError
    ) -> None:
        """Update common context patterns."""
        for key, value in error.context.execution_context.items():
            if key in pattern.common_contexts:
                if pattern.common_contexts[key] != value:
                    del pattern.common_contexts[key]

    def _generate_fix_suggestions(self, pattern: ErrorPattern) -> List[str]:
        """Generate fix suggestions based on error pattern."""
        suggestions = []

        if pattern.error_category == ErrorCategory.VALIDATION:
            suggestions.extend(
                [
                    "Add input validation before processing",
                    "Implement schema validation for data structures",
                    "Add type checking for function parameters",
                ]
            )
        elif pattern.error_category == ErrorCategory.NETWORK:
            suggestions.extend(
                [
                    "Implement retry logic with exponential backoff",
                    "Add connection timeout configuration",
                    "Check network connectivity and DNS resolution",
                ]
            )
        elif pattern.error_category == ErrorCategory.PLUGIN:
            suggestions.extend(
                [
                    "Configure fallback plugins for critical operations",
                    "Add plugin health checks before execution",
                    "Review plugin configuration and dependencies",
                ]
            )
        elif pattern.error_category == ErrorCategory.RESOURCE:
            suggestions.extend(
                [
                    "Monitor resource usage and implement limits",
                    "Add resource cleanup after operations",
                    "Consider using resource pooling",
                ]
            )
        elif pattern.error_category == ErrorCategory.TIMEOUT:
            suggestions.extend(
                [
                    "Increase timeout values for slow operations",
                    "Implement async processing for long tasks",
                    "Add progress indicators and cancellation support",
                ]
            )

        if "sandbox" in pattern.affected_stages:
            suggestions.append("Review sandbox security policies and resource limits")
        if "think" in pattern.affected_stages:
            suggestions.append(
                "Consider simpler reasoning strategies for complex problems"
            )

        for plugin in pattern.affected_plugins:
            if "llm" in plugin.lower():
                suggestions.append("Check LLM service availability and rate limits")
            elif "tool" in plugin.lower():
                suggestions.append("Validate tool inputs and environment setup")

        return list(set(suggestions))

    def get_error_patterns(self, min_occurrences: int = 1) -> List[ErrorPattern]:
        """Get error patterns meeting minimum occurrence threshold."""
        return [
            pattern
            for pattern in self.patterns.values()
            if pattern.occurrences >= min_occurrences
        ]

    def get_recovery_suggestions(self, error: PipelineError) -> List[RecoveryStrategy]:
        """Get recovery strategy suggestions for a specific error."""
        applicable_strategies = []

        for strategy in self.recovery_strategies:
            if error.category in strategy.applicable_categories:
                applicable_strategies.append(strategy)

        return sorted(applicable_strategies, key=lambda s: s.success_rate, reverse=True)

    def analyze_recent_errors(
        self, time_window: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """Analyze recent errors for trends and issues."""
        cutoff_time = datetime.now() - time_window
        recent_errors = [
            error
            for error in self.error_history
            if error.context.timestamp >= cutoff_time
        ]

        if not recent_errors:
            return {
                "status": "no_recent_errors",
                "window_hours": time_window.total_seconds() / 3600,
            }

        by_category = defaultdict(list)
        by_stage = defaultdict(list)
        by_plugin = defaultdict(list)

        for error in recent_errors:
            by_category[error.category.value].append(error)
            by_stage[error.stage].append(error)
            if error.plugin:
                by_plugin[error.plugin].append(error)

        return {
            "status": "analysis_complete",
            "window_hours": time_window.total_seconds() / 3600,
            "total_errors": len(recent_errors),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "by_stage": {k: len(v) for k, v in by_stage.items()},
            "by_plugin": {k: len(v) for k, v in by_plugin.items()},
            "top_error_types": self._get_top_error_types(recent_errors),
            "severity_distribution": self._get_severity_distribution(recent_errors),
            "recommendations": self._generate_trend_recommendations(
                by_category, by_stage
            ),
        }

    def _get_top_error_types(
        self, errors: List[PipelineError]
    ) -> List[Tuple[str, int]]:
        """Get most common error types."""
        error_counts = defaultdict(int)
        for error in errors:
            error_type = error.original_error.__class__.__name__
            error_counts[error_type] += 1

        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def _get_severity_distribution(self, errors: List[PipelineError]) -> Dict[str, int]:
        """Get distribution of error severities."""
        distribution = defaultdict(int)
        for error in errors:
            distribution[error.severity.value] += 1
        return dict(distribution)

    def _generate_trend_recommendations(
        self,
        by_category: Dict[str, List[PipelineError]],
        by_stage: Dict[str, List[PipelineError]],
    ) -> List[str]:
        """Generate recommendations based on error trends."""
        recommendations = []

        for category, errors in by_category.items():
            if len(errors) >= 2:
                if category == "network":
                    recommendations.append(
                        "Consider implementing network resilience patterns"
                    )
                elif category == "plugin":
                    recommendations.append(
                        "Review plugin stability and add health checks"
                    )
                elif category == "validation":
                    recommendations.append(
                        "Strengthen input validation at entry points"
                    )

        for stage, errors in by_stage.items():
            if len(errors) >= 2:
                recommendations.append(
                    f"Stage '{stage}' shows high error rate - investigate configuration"
                )

        return recommendations

    def generate_debug_report(self, request_id: str) -> str:
        """Generate a debug report for a specific request."""
        request_errors = [
            error
            for error in self.error_history
            if error.context.request_id == request_id
        ]

        if not request_errors:
            return f"No errors found for request ID: {request_id}"

        lines = [
            f"Debug Report for Request ID: {request_id}",
            "=" * 50,
            f"Total Errors: {len(request_errors)}",
            "",
        ]

        for i, error in enumerate(request_errors, 1):
            lines.extend(
                [
                    f"Error {i}:",
                    f"  Stage: {error.stage}",
                    f"  Plugin: {error.plugin or 'N/A'}",
                    f"  Category: {error.category.value}",
                    f"  Severity: {error.severity.value}",
                    f"  Time: {error.context.timestamp}",
                    f"  Plugin Stack: {' -> '.join(error.context.plugin_stack)}",
                    f"  Message: {error.original_error}",
                    "",
                ]
            )

        if request_errors:
            last_error = request_errors[-1]
            suggestions = self.get_recovery_suggestions(last_error)
            if suggestions:
                lines.extend(["Recovery Suggestions:", "-" * 20])
                for suggestion in suggestions[:3]:
                    lines.extend(
                        [
                            f"• {suggestion.name}: {suggestion.description}",
                            f"  Success Rate: {suggestion.success_rate:.1%}",
                            "",
                        ]
                    )

        return "\n".join(lines)


error_analyzer = ErrorAnalyzer()
