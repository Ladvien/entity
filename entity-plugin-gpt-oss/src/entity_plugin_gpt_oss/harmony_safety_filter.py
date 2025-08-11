"""Harmony Safety Filter Plugin for GPT-OSS Chain-of-Thought Content.

This plugin implements comprehensive safety filtering for gpt-oss chain-of-thought
content according to OpenAI's safety guidelines. It filters potentially harmful
content while preserving reasoning quality indicators and providing audit logging.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class SafetyCategory(Enum):
    """Categories of safety violations to detect and filter."""

    HARMFUL_CONTENT = "harmful_content"
    EXPLOIT_INSTRUCTIONS = "exploit_instructions"
    UNETHICAL_REASONING = "unethical_reasoning"
    PRIVACY_VIOLATIONS = "privacy_violations"
    ILLEGAL_ACTIVITIES = "illegal_activities"
    VIOLENCE_PROMOTION = "violence_promotion"
    HATE_SPEECH = "hate_speech"
    SELF_HARM = "self_harm"
    DANGEROUS_INSTRUCTIONS = "dangerous_instructions"


class SafetySeverity(Enum):
    """Severity levels for safety violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyViolation(BaseModel):
    """Represents a detected safety violation."""

    category: SafetyCategory = Field(description="Category of safety violation")
    severity: SafetySeverity = Field(description="Severity level of violation")
    pattern_matched: str = Field(description="Pattern that triggered the violation")
    matched_text: str = Field(description="Text that matched the pattern")
    confidence_score: float = Field(
        description="Confidence in violation detection", ge=0.0, le=1.0
    )
    position: int = Field(description="Character position in content")
    context: str = Field(description="Surrounding context of violation")


class SafetyFilterResult(BaseModel):
    """Result of safety filtering operation."""

    filtered_content: str = Field(description="Content after safety filtering")
    original_length: int = Field(description="Length of original content")
    filtered_length: int = Field(description="Length of filtered content")
    violations_detected: List[SafetyViolation] = Field(
        description="List of detected violations"
    )
    filter_applied: bool = Field(description="Whether any filtering was applied")
    reasoning_quality_preserved: bool = Field(
        description="Whether reasoning quality indicators were preserved"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional filtering metadata"
    )


class HarmonySafetyFilterPlugin(Plugin):
    """Plugin that filters harmful content from gpt-oss chain-of-thought.

    This plugin runs in the PARSE stage to filter potentially harmful content
    from gpt-oss chain-of-thought outputs while preserving reasoning quality
    and providing comprehensive audit logging.
    """

    supported_stages = [WorkflowExecutor.PARSE]

    class ConfigModel(BaseModel):
        """Configuration for the harmony safety filter plugin."""

        # Core filtering settings
        enabled: bool = Field(default=True, description="Enable safety filtering")
        strict_mode: bool = Field(
            default=False, description="Enable strict safety filtering mode"
        )
        preserve_reasoning_quality: bool = Field(
            default=True, description="Preserve reasoning quality indicators"
        )

        # Safety categories and thresholds
        enabled_categories: List[str] = Field(
            default_factory=lambda: [cat.value for cat in SafetyCategory],
            description="Enabled safety categories",
        )
        severity_thresholds: Dict[str, str] = Field(
            default_factory=lambda: {
                SafetyCategory.HARMFUL_CONTENT.value: SafetySeverity.LOW.value,
                SafetyCategory.EXPLOIT_INSTRUCTIONS.value: SafetySeverity.MEDIUM.value,
                SafetyCategory.VIOLENCE_PROMOTION.value: SafetySeverity.HIGH.value,
            },
            description="Minimum severity to trigger filtering by category",
        )
        confidence_threshold: float = Field(
            default=0.7,
            description="Minimum confidence to trigger filtering",
            ge=0.0,
            le=1.0,
        )

        # Content processing
        max_context_length: int = Field(
            default=100, description="Length of context to preserve around violations"
        )
        replacement_strategy: str = Field(
            default="placeholder",
            description="Strategy for replacing filtered content",
            pattern="^(placeholder|redaction|removal|warning)$",
        )
        placeholder_text: str = Field(
            default="[Content filtered for safety - reasoning preserved]",
            description="Text to use when replacing filtered content",
        )

        # Reasoning preservation
        reasoning_indicators: List[str] = Field(
            default_factory=lambda: [
                "therefore",
                "because",
                "since",
                "due to",
                "as a result",
                "consequently",
                "thus",
                "hence",
                "reasoning",
                "analysis",
                "conclusion",
                "evidence",
                "rationale",
                "logic",
                "step",
            ],
            description="Terms that indicate reasoning quality",
        )
        preserve_reasoning_context: bool = Field(
            default=True,
            description="Preserve context around reasoning indicators",
        )
        reasoning_context_radius: int = Field(
            default=50, description="Characters to preserve around reasoning indicators"
        )

        # Audit and logging
        enable_audit_logging: bool = Field(
            default=True, description="Enable comprehensive audit logging"
        )
        log_all_violations: bool = Field(
            default=True, description="Log all detected violations"
        )
        log_filtered_content: bool = Field(
            default=False, description="Log the actual filtered content (privacy risk)"
        )
        audit_retention_days: int = Field(
            default=30, description="Days to retain audit logs"
        )

        # Performance and limits
        max_content_length: int = Field(
            default=50000, description="Maximum content length to process"
        )
        processing_timeout_seconds: float = Field(
            default=5.0, description="Timeout for processing content"
        )
        enable_caching: bool = Field(
            default=True, description="Cache filtering results for performance"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the harmony safety filter plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize safety patterns by category
        self._safety_patterns = self._initialize_safety_patterns()

        # Initialize audit log
        self._audit_log: List[Dict[str, Any]] = []

        # Initialize content cache for performance
        self._content_cache: Dict[str, SafetyFilterResult] = {}

    def _initialize_safety_patterns(self) -> Dict[SafetyCategory, List[Dict[str, Any]]]:
        """Initialize safety detection patterns by category."""
        return {
            SafetyCategory.HARMFUL_CONTENT: [
                {
                    "pattern": r"(?i)\b(harmful|dangerous|toxic|malicious)\s+(content|information|instructions?)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.8,
                },
                {
                    "pattern": r"(?i)how\s+to\s+(harm|hurt|damage|destroy)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
                {
                    "pattern": r"(?i)step[-\s]by[-\s]step.*?(harmful|dangerous|illegal)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.85,
                },
            ],
            SafetyCategory.EXPLOIT_INSTRUCTIONS: [
                {
                    "pattern": r"(?i)(exploit|vulnerability|bypass.*security)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.8,
                },
                {
                    "pattern": r"(?i)detailed.*?(hack|crack|break\s+into)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
                {
                    "pattern": r"(?i)(unauthorized\s+access|penetration\s+testing)",
                    "severity": SafetySeverity.MEDIUM,
                    "confidence": 0.7,
                },
            ],
            SafetyCategory.UNETHICAL_REASONING: [
                {
                    "pattern": r"(?i)(unethical|immoral|wrong)\s+(reasoning|approach|method)",
                    "severity": SafetySeverity.MEDIUM,
                    "confidence": 0.75,
                },
                {
                    "pattern": r"(?i)reasoning.*?(deceive|mislead|manipulate)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.85,
                },
            ],
            SafetyCategory.PRIVACY_VIOLATIONS: [
                {
                    "pattern": r"(?i)(personal\s+information|private\s+data).*?(extract|collect|gather)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.8,
                },
                {
                    "pattern": r"(?i)(social\s+security|credit\s+card|ssn|phone\s+number)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
            ],
            SafetyCategory.ILLEGAL_ACTIVITIES: [
                {
                    "pattern": r"(?i)(illegal|unlawful|criminal)\s+(activities?|actions?|methods?)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.85,
                },
                {
                    "pattern": r"(?i)how\s+to.*?(steal|rob|fraud|scam)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
            ],
            SafetyCategory.VIOLENCE_PROMOTION: [
                {
                    "pattern": r"(?i)(violence|aggression|attack).*?(promote|encourage|incite)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
                {
                    "pattern": r"(?i)(weapon|bomb|explosive).*?(make|build|create)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.95,
                },
            ],
            SafetyCategory.HATE_SPEECH: [
                {
                    "pattern": r"(?i)(hate|discrimination).*?(based\s+on|targeting)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.8,
                },
                {
                    "pattern": r"(?i)(racist|sexist|homophobic)\s+(content|reasoning|approach)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.85,
                },
            ],
            SafetyCategory.SELF_HARM: [
                {
                    "pattern": r"(?i)(self[-\s]harm|suicide|self[-\s]injury)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
                {
                    "pattern": r"(?i)how\s+to.*?(hurt\s+yourself|end\s+your\s+life)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.95,
                },
            ],
            SafetyCategory.DANGEROUS_INSTRUCTIONS: [
                {
                    "pattern": r"(?i)(dangerous|hazardous)\s+(instructions?|procedures?|steps?)",
                    "severity": SafetySeverity.HIGH,
                    "confidence": 0.8,
                },
                {
                    "pattern": r"(?i)bypass.*?(safety|security|protection)",
                    "severity": SafetySeverity.CRITICAL,
                    "confidence": 0.9,
                },
            ],
        }

    async def _execute_impl(self, context) -> str:
        """Execute safety filtering on the input message.

        Args:
            context: Plugin execution context

        Returns:
            Filtered message content
        """
        try:
            if not self.config.enabled:
                return context.message

            # Check content length limits
            if len(context.message) > self.config.max_content_length:
                await self._log_audit_entry(
                    "content_too_long",
                    context,
                    {
                        "original_length": len(context.message),
                        "limit": self.config.max_content_length,
                    },
                )
                return context.message  # Skip filtering for oversized content

            # Check cache first
            cache_key = self._generate_cache_key(context.message)
            if self.config.enable_caching and cache_key in self._content_cache:
                cached_result = self._content_cache[cache_key]
                await self._log_audit_entry(
                    "cache_hit", context, {"cache_key": cache_key}
                )
                return cached_result.filtered_content

            # Perform safety filtering
            filter_result = await self._filter_content(context.message, context)

            # Cache the result
            if self.config.enable_caching:
                self._content_cache[cache_key] = filter_result
                # Implement simple LRU cache limit
                if len(self._content_cache) > 100:
                    oldest_key = next(iter(self._content_cache))
                    del self._content_cache[oldest_key]

            # Log filtering result
            await self._log_audit_entry(
                "filtering_completed",
                context,
                {
                    "violations_count": len(filter_result.violations_detected),
                    "filter_applied": filter_result.filter_applied,
                    "reasoning_preserved": filter_result.reasoning_quality_preserved,
                    "original_length": filter_result.original_length,
                    "filtered_length": filter_result.filtered_length,
                },
            )

            # Log individual violations if enabled
            if self.config.log_all_violations:
                for violation in filter_result.violations_detected:
                    await self._log_violation(violation, context)

            return filter_result.filtered_content

        except Exception as e:
            # Log error and return original content to avoid breaking the pipeline
            await context.log(
                level="error",
                category="harmony_safety_filter",
                message=f"Safety filtering error: {str(e)}",
                error=str(e),
            )
            return context.message

    async def _filter_content(self, content: str, context) -> SafetyFilterResult:
        """Filter content for safety violations.

        Args:
            content: Content to filter
            context: Plugin execution context

        Returns:
            Safety filtering result
        """
        violations: List[SafetyViolation] = []
        filtered_content = content
        original_length = len(content)

        # Detect violations across all enabled categories
        for category in SafetyCategory:
            if category.value not in self.config.enabled_categories:
                continue

            category_violations = await self._detect_violations_in_category(
                content, category
            )
            violations.extend(category_violations)

        # Sort violations by position for proper replacement
        violations.sort(key=lambda v: v.position, reverse=True)

        # Apply filtering based on severity and confidence thresholds
        filter_applied = False
        for violation in violations:
            if (
                violation.confidence_score >= self.config.confidence_threshold
                and self._should_filter_violation(violation)
            ):
                filtered_content = await self._apply_violation_filter(
                    filtered_content, violation, context
                )
                filter_applied = True

        # Preserve reasoning quality if enabled
        reasoning_preserved = False
        if self.config.preserve_reasoning_quality and filter_applied:
            (
                filtered_content,
                reasoning_preserved,
            ) = await self._preserve_reasoning_quality(
                content, filtered_content, context
            )

        return SafetyFilterResult(
            filtered_content=filtered_content,
            original_length=original_length,
            filtered_length=len(filtered_content),
            violations_detected=violations,
            filter_applied=filter_applied,
            reasoning_quality_preserved=reasoning_preserved,
            metadata={
                "processing_timestamp": datetime.now().isoformat(),
                "categories_checked": self.config.enabled_categories,
                "confidence_threshold": self.config.confidence_threshold,
            },
        )

    async def _detect_violations_in_category(
        self, content: str, category: SafetyCategory
    ) -> List[SafetyViolation]:
        """Detect safety violations in a specific category."""
        violations = []
        patterns = self._safety_patterns.get(category, [])

        for pattern_config in patterns:
            pattern = pattern_config["pattern"]
            severity = pattern_config["severity"]
            confidence = pattern_config["confidence"]

            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                matched_text = match.group(0)
                position = match.start()

                # Extract context around the match
                context_start = max(0, position - self.config.max_context_length // 2)
                context_end = min(
                    len(content),
                    position + len(matched_text) + self.config.max_context_length // 2,
                )
                context_text = content[context_start:context_end]

                violation = SafetyViolation(
                    category=category,
                    severity=severity,
                    pattern_matched=pattern,
                    matched_text=matched_text,
                    confidence_score=confidence,
                    position=position,
                    context=context_text,
                )
                violations.append(violation)

        return violations

    def _should_filter_violation(self, violation: SafetyViolation) -> bool:
        """Determine if a violation should trigger filtering."""
        # Check if severity meets threshold
        category_threshold = self.config.severity_thresholds.get(
            violation.category.value, SafetySeverity.MEDIUM.value
        )

        severity_levels = {
            SafetySeverity.LOW: 1,
            SafetySeverity.MEDIUM: 2,
            SafetySeverity.HIGH: 3,
            SafetySeverity.CRITICAL: 4,
        }

        violation_level = severity_levels.get(violation.severity, 2)
        threshold_level = severity_levels.get(SafetySeverity(category_threshold), 2)

        return violation_level >= threshold_level

    async def _apply_violation_filter(
        self, content: str, violation: SafetyViolation, context
    ) -> str:
        """Apply filtering for a specific violation."""
        strategy = self.config.replacement_strategy

        if strategy == "placeholder":
            replacement = self.config.placeholder_text
        elif strategy == "redaction":
            replacement = "[REDACTED]"
        elif strategy == "removal":
            replacement = ""
        elif strategy == "warning":
            replacement = f"[WARNING: {violation.category.value} content filtered]"
        else:
            replacement = self.config.placeholder_text

        # Replace the matched text with the appropriate replacement
        start = violation.position
        end = start + len(violation.matched_text)
        filtered_content = content[:start] + replacement + content[end:]

        return filtered_content

    async def _preserve_reasoning_quality(
        self, original_content: str, filtered_content: str, context
    ) -> tuple[str, bool]:
        """Preserve reasoning quality indicators in filtered content."""
        if not self.config.preserve_reasoning_context:
            return filtered_content, False

        preserved_segments = []
        reasoning_preserved = False

        for indicator in self.config.reasoning_indicators:
            pattern = rf"\b{re.escape(indicator)}\b"
            for match in re.finditer(pattern, original_content, re.IGNORECASE):
                start = max(0, match.start() - self.config.reasoning_context_radius)
                end = min(
                    len(original_content),
                    match.end() + self.config.reasoning_context_radius,
                )
                segment = original_content[start:end].strip()

                # Check if this segment was filtered out
                if segment not in filtered_content:
                    preserved_segments.append(f"[Reasoning: {segment}]")
                    reasoning_preserved = True

        if preserved_segments:
            # Append preserved reasoning segments
            filtered_content += "\n\n" + "\n".join(preserved_segments)

        return filtered_content, reasoning_preserved

    def _generate_cache_key(self, content: str) -> str:
        """Generate cache key for content."""
        import hashlib

        return hashlib.md5(content.encode()).hexdigest()

    async def _log_audit_entry(
        self, action: str, context, metadata: Dict[str, Any] = None
    ) -> None:
        """Log audit entry for safety filtering actions."""
        if not self.config.enable_audit_logging:
            return

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_id": getattr(context, "user_id", "unknown"),
            "execution_id": getattr(context, "execution_id", "unknown"),
            "metadata": metadata or {},
        }

        self._audit_log.append(audit_entry)

        # Log to context logging system
        await context.log(
            level="info",
            category="harmony_safety_filter_audit",
            message=f"Safety filter audit: {action}",
            **audit_entry,
        )

        # Cleanup old audit entries
        await self._cleanup_old_audit_entries()

    async def _log_violation(self, violation: SafetyViolation, context) -> None:
        """Log individual safety violation."""
        violation_data = {
            "category": violation.category.value,
            "severity": violation.severity.value,
            "confidence": violation.confidence_score,
            "position": violation.position,
        }

        # Only log actual content if explicitly enabled (privacy consideration)
        if self.config.log_filtered_content:
            violation_data["matched_text"] = violation.matched_text
            violation_data["context"] = violation.context

        await context.log(
            level="warning",
            category="harmony_safety_violation",
            message=f"Safety violation detected: {violation.category.value}",
            violation_category=violation.category.value,
            violation_severity=violation.severity.value,
            violation_confidence=violation.confidence_score,
            violation_position=violation.position,
            **(
                {"matched_text": violation.matched_text, "context": violation.context}
                if self.config.log_filtered_content
                else {}
            ),
        )

    async def _cleanup_old_audit_entries(self) -> None:
        """Remove old audit entries based on retention policy."""
        if not self.config.audit_retention_days:
            return

        retention_cutoff = datetime.now().timestamp() - (
            self.config.audit_retention_days * 24 * 60 * 60
        )

        self._audit_log = [
            entry
            for entry in self._audit_log
            if datetime.fromisoformat(entry["timestamp"]).timestamp() > retention_cutoff
        ]

    # Public API methods for external usage

    async def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety filtering statistics."""
        return {
            "enabled_categories": self.config.enabled_categories,
            "confidence_threshold": self.config.confidence_threshold,
            "severity_thresholds": self.config.severity_thresholds,
            "audit_entries_count": len(self._audit_log),
            "cache_size": len(self._content_cache) if self.config.enable_caching else 0,
            "patterns_loaded": sum(
                len(patterns) for patterns in self._safety_patterns.values()
            ),
        }

    async def test_content_safety(self, content: str) -> SafetyFilterResult:
        """Test content for safety violations without applying filters."""

        # Create minimal context for testing
        class MockContext:
            def __init__(self):
                self.user_id = "test_user"
                self.execution_id = "test_execution"

            async def log(self, **kwargs):
                pass

        mock_context = MockContext()
        return await self._filter_content(content, mock_context)

    async def add_custom_pattern(
        self,
        category: SafetyCategory,
        pattern: str,
        severity: SafetySeverity,
        confidence: float,
    ) -> bool:
        """Add custom safety pattern."""
        try:
            re.compile(pattern)  # Validate pattern

            if category not in self._safety_patterns:
                self._safety_patterns[category] = []

            self._safety_patterns[category].append(
                {
                    "pattern": pattern,
                    "severity": severity,
                    "confidence": confidence,
                }
            )

            return True
        except re.error:
            return False

    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        if limit:
            return self._audit_log[-limit:]
        return self._audit_log.copy()
