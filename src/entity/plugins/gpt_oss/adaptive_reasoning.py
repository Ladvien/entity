"""Adaptive Reasoning Controller Plugin for GPT-OSS integration.

This plugin dynamically adjusts gpt-oss's reasoning level (low/medium/high) based
on task complexity analysis and performance requirements, optimizing the balance
between performance and accuracy.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class ReasoningEffort(Enum):
    """Reasoning effort levels for GPT-OSS."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplexityFactors(BaseModel):
    """Factors contributing to task complexity."""

    message_length: int = Field(description="Length of the message in characters")
    word_count: int = Field(description="Number of words in the message")
    sentence_count: int = Field(description="Number of sentences")
    question_count: int = Field(description="Number of questions")
    technical_terms_count: int = Field(description="Number of technical terms")
    code_blocks_count: int = Field(description="Number of code blocks")
    math_expressions_count: int = Field(description="Number of math expressions")
    nested_structures: int = Field(
        description="Level of nested structures (lists, etc)"
    )
    ambiguity_score: float = Field(description="Ambiguity score (0-1)", ge=0, le=1)
    domain_specificity: float = Field(
        description="Domain specificity score (0-1)", ge=0, le=1
    )


class ComplexityScore(BaseModel):
    """Task complexity analysis result."""

    overall_score: float = Field(
        description="Overall complexity score (0-1)", ge=0, le=1
    )
    factors: ComplexityFactors = Field(description="Individual complexity factors")
    reasoning_level: ReasoningEffort = Field(description="Recommended reasoning level")
    confidence: float = Field(
        description="Confidence in the recommendation (0-1)", ge=0, le=1
    )
    analysis_time_ms: float = Field(
        description="Time taken for analysis in milliseconds"
    )


class ReasoningDecision(BaseModel):
    """A reasoning level decision with metadata."""

    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: str = Field(description="Unique task identifier")
    complexity_score: ComplexityScore = Field(description="Complexity analysis result")
    selected_level: ReasoningEffort = Field(description="Selected reasoning level")
    override_reason: Optional[str] = Field(
        default=None, description="Reason if manually overridden"
    )
    estimated_tokens: int = Field(description="Estimated token usage")
    estimated_latency_ms: float = Field(description="Estimated latency in milliseconds")


class PerformanceMetrics(BaseModel):
    """Performance metrics for reasoning decisions."""

    total_decisions: int = Field(default=0)
    low_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    high_count: int = Field(default=0)
    average_complexity: float = Field(default=0.0)
    average_tokens: float = Field(default=0.0)
    average_latency_ms: float = Field(default=0.0)
    override_count: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.now)


class AdaptiveReasoningPlugin(Plugin):
    """Plugin that dynamically adjusts reasoning effort based on task complexity.

    This plugin:
    - Analyzes task complexity using multiple heuristics
    - Adjusts reasoning level dynamically (low/medium/high)
    - Monitors token usage and latency patterns
    - Provides data-driven reasoning level recommendations
    - Supports manual override via context
    - Maintains detailed logs for analysis and optimization
    """

    supported_stages = [WorkflowExecutor.PARSE]
    dependencies = ["llm", "memory"]

    class ConfigModel(BaseModel):
        """Configuration for the adaptive reasoning controller."""

        # Complexity thresholds
        low_complexity_threshold: float = Field(
            default=0.3, description="Threshold for low complexity", ge=0, le=1
        )
        high_complexity_threshold: float = Field(
            default=0.7, description="Threshold for high complexity", ge=0, le=1
        )

        # Performance targets
        target_latency_ms: float = Field(
            default=2000.0, description="Target latency in milliseconds"
        )
        max_tokens_low: int = Field(
            default=500, description="Max tokens for low reasoning"
        )
        max_tokens_medium: int = Field(
            default=1500, description="Max tokens for medium reasoning"
        )
        max_tokens_high: int = Field(
            default=4000, description="Max tokens for high reasoning"
        )

        # Adaptation settings
        enable_adaptive_adjustment: bool = Field(
            default=True, description="Enable dynamic adaptation based on performance"
        )
        learning_rate: float = Field(
            default=0.1,
            description="Learning rate for threshold adaptation",
            ge=0,
            le=1,
        )
        history_window: int = Field(
            default=100, description="Number of decisions to consider for adaptation"
        )

        # Analysis weights
        length_weight: float = Field(
            default=0.2, description="Weight for message length"
        )
        question_weight: float = Field(default=0.3, description="Weight for questions")
        technical_weight: float = Field(
            default=0.25, description="Weight for technical content"
        )
        structure_weight: float = Field(
            default=0.15, description="Weight for structural complexity"
        )
        ambiguity_weight: float = Field(default=0.1, description="Weight for ambiguity")

        # Override settings
        allow_manual_override: bool = Field(
            default=True, description="Allow manual reasoning level override"
        )
        respect_user_preference: bool = Field(
            default=True, description="Respect user's reasoning level preference"
        )

        # Logging settings
        enable_decision_logging: bool = Field(
            default=True, description="Enable logging of reasoning decisions"
        )
        log_detailed_analysis: bool = Field(
            default=False, description="Log detailed complexity analysis"
        )
        metrics_update_interval: int = Field(
            default=10, description="Decisions between metrics updates"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the adaptive reasoning controller plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize technical terms list
        self.technical_terms = self._load_technical_terms()

        # Initialize performance tracking
        self.recent_decisions: List[ReasoningDecision] = []
        self.performance_metrics = PerformanceMetrics()

    def _load_technical_terms(self) -> set:
        """Load technical terms for complexity analysis."""
        # Common technical terms across various domains
        return {
            # Programming
            "algorithm",
            "function",
            "variable",
            "class",
            "method",
            "object",
            "array",
            "loop",
            "recursion",
            "exception",
            "interface",
            "inheritance",
            "polymorphism",
            "encapsulation",
            "abstraction",
            "compile",
            "runtime",
            "debug",
            "optimize",
            "refactor",
            "api",
            "framework",
            "library",
            # Data Science / ML
            "model",
            "training",
            "validation",
            "dataset",
            "feature",
            "label",
            "neural",
            "network",
            "gradient",
            "backpropagation",
            "overfitting",
            "regularization",
            "hyperparameter",
            "classification",
            "regression",
            "clustering",
            "dimensionality",
            "embedding",
            "transformer",
            "attention",
            # Math/Science
            "equation",
            "derivative",
            "integral",
            "matrix",
            "vector",
            "theorem",
            "hypothesis",
            "correlation",
            "probability",
            "distribution",
            "variance",
            "coefficient",
            "polynomial",
            "exponential",
            "logarithm",
            "quantum",
            # System/Infrastructure
            "database",
            "query",
            "index",
            "transaction",
            "cache",
            "latency",
            "throughput",
            "scalability",
            "concurrency",
            "synchronization",
            "microservice",
            "container",
            "orchestration",
            "deployment",
            "pipeline",
        }

    async def _execute_impl(self, context) -> str:
        """Execute adaptive reasoning logic in PARSE stage."""
        user_id = context.user_id
        message = context.message
        task_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Check for manual override
            manual_level = None
            if self.config.allow_manual_override:
                manual_level = await context.recall("reasoning_level_override", None)

            # Check for user preference
            user_preference = None
            if self.config.respect_user_preference:
                user_preference = await context.recall(
                    f"user_reasoning_preference:{user_id}", None
                )

            # Analyze task complexity
            start_time = time.time()
            complexity_score = await self._analyze_complexity(message)
            analysis_time_ms = (time.time() - start_time) * 1000
            complexity_score.analysis_time_ms = analysis_time_ms

            # Determine reasoning level
            if manual_level:
                selected_level = ReasoningEffort(manual_level)
                override_reason = "Manual override"
            elif user_preference:
                selected_level = ReasoningEffort(user_preference)
                override_reason = "User preference"
            else:
                selected_level = await self._determine_reasoning_level(
                    complexity_score, context
                )
                override_reason = None

            # Estimate performance impact
            estimated_tokens = self._estimate_tokens(selected_level, len(message))
            estimated_latency = self._estimate_latency(selected_level, complexity_score)

            # Create decision record
            decision = ReasoningDecision(
                task_id=task_id,
                complexity_score=complexity_score,
                selected_level=selected_level,
                override_reason=override_reason,
                estimated_tokens=estimated_tokens,
                estimated_latency_ms=estimated_latency,
            )

            # Store reasoning level for downstream plugins
            await context.remember("reasoning_level", selected_level.value)
            await context.remember("complexity_score", complexity_score.overall_score)
            await context.remember("reasoning_decision", decision.model_dump())

            # Log decision
            if self.config.enable_decision_logging:
                await self._log_decision(context, decision)

            # Update metrics
            await self._update_metrics(decision)

            # Adapt thresholds if enabled
            if self.config.enable_adaptive_adjustment:
                await self._adapt_thresholds()

            # Log summary
            await context.log(
                level="info",
                category="adaptive_reasoning",
                message=f"Selected reasoning level: {selected_level.value}",
                complexity_score=complexity_score.overall_score,
                confidence=complexity_score.confidence,
                estimated_tokens=estimated_tokens,
                estimated_latency_ms=estimated_latency,
                override=override_reason is not None,
            )

            return message

        except Exception as e:
            # Log error and use default reasoning level
            await context.log(
                level="error",
                category="adaptive_reasoning",
                message=f"Error in adaptive reasoning: {str(e)}",
                error=str(e),
            )

            # Use medium as safe default
            await context.remember("reasoning_level", ReasoningEffort.MEDIUM.value)
            return message

    async def _analyze_complexity(self, message: str) -> ComplexityScore:
        """Analyze the complexity of a task based on the message."""
        factors = ComplexityFactors(
            message_length=len(message),
            word_count=len(message.split()),
            sentence_count=len(re.findall(r"[.!?]+", message)) or 1,
            question_count=message.count("?"),
            technical_terms_count=self._count_technical_terms(message),
            code_blocks_count=message.count("```"),
            math_expressions_count=self._count_math_expressions(message),
            nested_structures=self._analyze_nesting(message),
            ambiguity_score=self._calculate_ambiguity(message),
            domain_specificity=self._calculate_domain_specificity(message),
        )

        # Calculate weighted complexity score
        overall_score = self._calculate_overall_complexity(factors)

        # Determine recommended reasoning level
        if overall_score < self.config.low_complexity_threshold:
            reasoning_level = ReasoningEffort.LOW
        elif overall_score > self.config.high_complexity_threshold:
            reasoning_level = ReasoningEffort.HIGH
        else:
            reasoning_level = ReasoningEffort.MEDIUM

        # Calculate confidence based on score distance from thresholds
        confidence = self._calculate_confidence(overall_score)

        return ComplexityScore(
            overall_score=overall_score,
            factors=factors,
            reasoning_level=reasoning_level,
            confidence=confidence,
            analysis_time_ms=0,  # Will be set by caller
        )

    def _count_technical_terms(self, message: str) -> int:
        """Count technical terms in the message."""
        words = message.lower().split()
        return sum(1 for word in words if word in self.technical_terms)

    def _count_math_expressions(self, message: str) -> int:
        """Count mathematical expressions in the message."""
        # Look for patterns like equations, formulas, etc.
        math_patterns = [
            r"\d+\s*[+\-*/]\s*\d+",  # Basic arithmetic
            r"[a-z]\s*=\s*",  # Variable assignments
            r"\b(sin|cos|tan|log|exp|sqrt)\b",  # Math functions
            r"\^|\*\*",  # Exponents
            r"\b\d+\.?\d*[eE][+-]?\d+\b",  # Scientific notation
        ]

        count = 0
        for pattern in math_patterns:
            count += len(re.findall(pattern, message, re.IGNORECASE))
        return count

    def _analyze_nesting(self, message: str) -> int:
        """Analyze the level of nested structures in the message."""
        # Count nested parentheses, brackets, etc.
        max_depth = 0
        current_depth = 0

        for char in message:
            if char in "([{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ")]}":
                current_depth = max(0, current_depth - 1)

        # Also check for nested lists (bullets, numbers)
        lines = message.split("\n")
        list_depth = 0
        for line in lines:
            indent_level = (len(line) - len(line.lstrip())) // 2
            if re.match(r"^\s*[-*•]\s", line) or re.match(r"^\s*\d+\.\s", line):
                list_depth = max(list_depth, indent_level)

        return max(max_depth, list_depth)

    def _calculate_ambiguity(self, message: str) -> float:
        """Calculate ambiguity score based on vague terms and unclear references."""
        ambiguous_terms = {
            "maybe",
            "perhaps",
            "might",
            "could",
            "possibly",
            "somewhat",
            "kind of",
            "sort of",
            "basically",
            "essentially",
            "roughly",
            "approximately",
            "about",
            "around",
            "various",
            "several",
            "some",
            "many",
            "few",
            "often",
            "sometimes",
            "usually",
            "it",
            "this",
            "that",
            "these",
            "those",
            "they",
            "them",
        }

        words = message.lower().split()
        if not words:
            return 0.0

        ambiguous_count = sum(1 for word in words if word in ambiguous_terms)

        # Also check for questions without clear context
        short_questions = len(re.findall(r"\b\w{1,5}\?", message))

        ambiguity_score = min(
            1.0, (ambiguous_count / len(words)) + (short_questions * 0.1)
        )
        return ambiguity_score

    def _calculate_domain_specificity(self, message: str) -> float:
        """Calculate how domain-specific the message is."""
        # Ratio of technical terms to total words
        words = message.split()
        if not words:
            return 0.0

        technical_ratio = self._count_technical_terms(message) / len(words)

        # Check for domain-specific patterns
        has_code = (
            "```" in message or "function" in message.lower() or "def " in message
        )
        has_math = (
            bool(re.search(r"[∫∑∏√∞±≈≠≤≥]", message)) or "equation" in message.lower()
        )
        has_data = any(
            term in message.lower() for term in ["dataset", "dataframe", "csv", "json"]
        )

        specificity = min(
            1.0,
            technical_ratio * 2
            + (0.2 if has_code else 0)
            + (0.2 if has_math else 0)
            + (0.1 if has_data else 0),
        )

        return specificity

    def _calculate_overall_complexity(self, factors: ComplexityFactors) -> float:
        """Calculate overall complexity score from individual factors."""
        # Normalize factors
        length_norm = min(1.0, factors.message_length / 1000)  # Normalize to 1000 chars
        question_norm = min(1.0, factors.question_count / 3)  # 3+ questions is complex
        technical_norm = min(
            1.0, factors.technical_terms_count / 10
        )  # 10+ terms is complex
        structure_norm = min(
            1.0, (factors.code_blocks_count + factors.nested_structures) / 5
        )

        # Apply weights
        weighted_score = (
            length_norm * self.config.length_weight
            + question_norm * self.config.question_weight
            + technical_norm * self.config.technical_weight
            + structure_norm * self.config.structure_weight
            + factors.ambiguity_score * self.config.ambiguity_weight
            + factors.domain_specificity * 0.2  # Additional factor
        )

        return min(1.0, weighted_score)

    def _calculate_confidence(self, score: float) -> float:
        """Calculate confidence based on distance from thresholds."""
        low_dist = abs(score - self.config.low_complexity_threshold)
        high_dist = abs(score - self.config.high_complexity_threshold)

        # Higher confidence when far from thresholds
        if score < self.config.low_complexity_threshold:
            confidence = min(1.0, low_dist * 3)
        elif score > self.config.high_complexity_threshold:
            confidence = min(1.0, high_dist * 3)
        else:
            # In medium range, confidence based on distance from both thresholds
            mid_point = (
                self.config.low_complexity_threshold
                + self.config.high_complexity_threshold
            ) / 2
            confidence = min(1.0, abs(score - mid_point) * 4)

        return confidence

    async def _determine_reasoning_level(
        self, complexity_score: ComplexityScore, context
    ) -> ReasoningEffort:
        """Determine the appropriate reasoning level based on complexity and performance."""
        base_level = complexity_score.reasoning_level

        if not self.config.enable_adaptive_adjustment:
            return base_level

        # Check recent performance
        if len(self.recent_decisions) >= 10:
            recent_latencies = [
                d.estimated_latency_ms for d in self.recent_decisions[-10:]
            ]
            avg_latency = sum(recent_latencies) / len(recent_latencies)

            # If we're consistently slow, consider reducing reasoning level
            if avg_latency > self.config.target_latency_ms * 1.5:
                if base_level == ReasoningEffort.HIGH:
                    await context.log(
                        level="info",
                        category="adaptive_reasoning",
                        message="Reducing reasoning level due to high latency",
                        avg_latency=avg_latency,
                        target_latency=self.config.target_latency_ms,
                    )
                    return ReasoningEffort.MEDIUM
                elif base_level == ReasoningEffort.MEDIUM:
                    return ReasoningEffort.LOW

        return base_level

    def _estimate_tokens(self, level: ReasoningEffort, message_length: int) -> int:
        """Estimate token usage based on reasoning level and message length."""
        # Base estimate from message
        base_tokens = message_length // 4  # Rough estimate: 4 chars per token

        # Multiply by reasoning level factor
        if level == ReasoningEffort.LOW:
            multiplier = 2
            max_tokens = self.config.max_tokens_low
        elif level == ReasoningEffort.MEDIUM:
            multiplier = 4
            max_tokens = self.config.max_tokens_medium
        else:  # HIGH
            multiplier = 8
            max_tokens = self.config.max_tokens_high

        estimated = base_tokens * multiplier
        return min(estimated, max_tokens)

    def _estimate_latency(
        self, level: ReasoningEffort, complexity: ComplexityScore
    ) -> float:
        """Estimate latency based on reasoning level and complexity."""
        # Base latency estimates
        if level == ReasoningEffort.LOW:
            base_latency = 500
        elif level == ReasoningEffort.MEDIUM:
            base_latency = 1500
        else:  # HIGH
            base_latency = 3000

        # Adjust based on complexity
        complexity_factor = 1 + (complexity.overall_score * 0.5)

        return base_latency * complexity_factor

    async def _log_decision(self, context, decision: ReasoningDecision) -> None:
        """Log reasoning decision for analysis."""
        # Store decision
        decision_key = f"reasoning_decision:{decision.task_id}"
        await context.remember(decision_key, decision.model_dump())

        # Add to recent decisions
        self.recent_decisions.append(decision)
        if len(self.recent_decisions) > self.config.history_window:
            self.recent_decisions.pop(0)

        # Log details if enabled
        if self.config.log_detailed_analysis:
            await context.log(
                level="debug",
                category="adaptive_reasoning_detail",
                message="Complexity analysis complete",
                factors=decision.complexity_score.factors.model_dump(),
                overall_score=decision.complexity_score.overall_score,
                selected_level=decision.selected_level.value,
                confidence=decision.complexity_score.confidence,
            )

    async def _update_metrics(self, decision: ReasoningDecision) -> None:
        """Update performance metrics."""
        self.performance_metrics.total_decisions += 1

        if decision.selected_level == ReasoningEffort.LOW:
            self.performance_metrics.low_count += 1
        elif decision.selected_level == ReasoningEffort.MEDIUM:
            self.performance_metrics.medium_count += 1
        else:
            self.performance_metrics.high_count += 1

        if decision.override_reason:
            self.performance_metrics.override_count += 1

        # Update averages
        n = self.performance_metrics.total_decisions
        self.performance_metrics.average_complexity = (
            self.performance_metrics.average_complexity * (n - 1)
            + decision.complexity_score.overall_score
        ) / n
        self.performance_metrics.average_tokens = (
            self.performance_metrics.average_tokens * (n - 1)
            + decision.estimated_tokens
        ) / n
        self.performance_metrics.average_latency_ms = (
            self.performance_metrics.average_latency_ms * (n - 1)
            + decision.estimated_latency_ms
        ) / n

        self.performance_metrics.last_updated = datetime.now()

        # Persist metrics periodically
        if (
            self.performance_metrics.total_decisions
            % self.config.metrics_update_interval
            == 0
        ):
            await self.resources["memory"].store(
                "adaptive_reasoning_metrics", self.performance_metrics.model_dump()
            )

    async def _adapt_thresholds(self) -> None:
        """Adapt complexity thresholds based on performance."""
        if len(self.recent_decisions) < 20:
            return  # Not enough data

        # Analyze recent performance
        recent = self.recent_decisions[-20:]
        avg_latency = sum(d.estimated_latency_ms for d in recent) / len(recent)

        # If we're consistently fast, we can afford more high reasoning
        if avg_latency < self.config.target_latency_ms * 0.7:
            # Lower the high threshold slightly
            self.config.high_complexity_threshold = max(
                0.5,
                self.config.high_complexity_threshold
                - self.config.learning_rate * 0.05,
            )
        # If we're consistently slow, reduce high reasoning
        elif avg_latency > self.config.target_latency_ms * 1.3:
            # Raise the high threshold slightly
            self.config.high_complexity_threshold = min(
                0.9,
                self.config.high_complexity_threshold
                + self.config.learning_rate * 0.05,
            )

    # Public API methods

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.model_dump()

    async def set_user_preference(self, user_id: str, level: ReasoningEffort) -> None:
        """Set a user's preferred reasoning level."""
        await self.resources["memory"].store(
            f"user_reasoning_preference:{user_id}", level.value
        )

    async def get_recent_decisions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent reasoning decisions."""
        recent = self.recent_decisions[-count:]
        return [d.model_dump() for d in recent]

    async def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze a message and return complexity score (for testing/debugging)."""
        score = await self._analyze_complexity(message)
        return score.model_dump()
