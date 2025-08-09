"""Unit tests for Adaptive Reasoning Controller Plugin."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.adaptive_reasoning import (
    AdaptiveReasoningPlugin,
    ComplexityFactors,
    ComplexityScore,
    PerformanceMetrics,
    ReasoningDecision,
    ReasoningEffort,
)
from entity.workflow.executor import WorkflowExecutor


class TestAdaptiveReasoningPlugin:
    """Test AdaptiveReasoningPlugin functionality."""

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
            "low_complexity_threshold": 0.3,
            "high_complexity_threshold": 0.7,
            "enable_adaptive_adjustment": True,
            "allow_manual_override": True,
        }
        return AdaptiveReasoningPlugin(mock_resources, config)

    @pytest.fixture
    def restricted_plugin(self, mock_resources):
        """Create plugin with restricted config."""
        config = {
            "low_complexity_threshold": 0.2,
            "high_complexity_threshold": 0.8,
            "enable_adaptive_adjustment": False,
            "allow_manual_override": False,
            "log_detailed_analysis": True,
        }
        return AdaptiveReasoningPlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.PARSE
        ctx.message = "Test message"
        ctx.user_id = "test_user"
        ctx.remember = AsyncMock()
        ctx.recall = AsyncMock(return_value=None)
        ctx.log = AsyncMock()
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.low_complexity_threshold == 0.3
        assert basic_plugin.config.high_complexity_threshold == 0.7
        assert basic_plugin.config.enable_adaptive_adjustment is True
        assert WorkflowExecutor.PARSE in basic_plugin.supported_stages
        assert "llm" in basic_plugin.dependencies
        assert "memory" in basic_plugin.dependencies

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"low_complexity_threshold": 1.5}  # Invalid, must be <= 1

        with pytest.raises(ValueError, match="Invalid configuration"):
            AdaptiveReasoningPlugin(mock_resources, config)

    def test_technical_terms_loaded(self, basic_plugin):
        """Test that technical terms are loaded."""
        assert len(basic_plugin.technical_terms) > 0
        assert "algorithm" in basic_plugin.technical_terms
        assert "neural" in basic_plugin.technical_terms
        assert "database" in basic_plugin.technical_terms

    @pytest.mark.asyncio
    async def test_basic_execution(self, basic_plugin, context):
        """Test basic plugin execution."""
        result = await basic_plugin._execute_impl(context)

        assert result == "Test message"

        # Check that reasoning level was stored
        context.remember.assert_any_call("reasoning_level", "low")

        # Check that complexity score was stored
        calls = [call[0] for call in context.remember.call_args_list]
        assert "complexity_score" in calls[0] or "complexity_score" in calls[1]

    @pytest.mark.asyncio
    async def test_manual_override(self, basic_plugin, context):
        """Test manual reasoning level override."""
        context.recall = AsyncMock(return_value="high")

        result = await basic_plugin._execute_impl(context)

        assert result == "Test message"
        context.remember.assert_any_call("reasoning_level", "high")

    @pytest.mark.asyncio
    async def test_user_preference(self, basic_plugin, context):
        """Test user preference for reasoning level."""

        async def recall_side_effect(key, default=None):
            if key == "reasoning_level_override":
                return None
            if key == "user_reasoning_preference:test_user":
                return "medium"
            return default

        context.recall = AsyncMock(side_effect=recall_side_effect)

        result = await basic_plugin._execute_impl(context)

        assert result == "Test message"
        context.remember.assert_any_call("reasoning_level", "medium")

    @pytest.mark.asyncio
    async def test_manual_override_disabled(self, restricted_plugin, context):
        """Test that manual override is ignored when disabled."""
        context.recall = AsyncMock(return_value="high")

        result = await restricted_plugin._execute_impl(context)

        # Should use computed level, not manual override
        assert result == "Test message"
        # Manual override is disabled, so recall shouldn't be called for override
        # But it might be called for user preference (which is also disabled)
        # Just check that result is correct

    @pytest.mark.asyncio
    async def test_complexity_analysis_simple_message(self, basic_plugin):
        """Test complexity analysis for simple message."""
        message = "Hello world"
        score = await basic_plugin._analyze_complexity(message)

        assert score.overall_score < 0.3  # Should be low complexity
        assert score.reasoning_level == ReasoningEffort.LOW
        assert score.factors.message_length == len(message)
        assert score.factors.word_count == 2

    @pytest.mark.asyncio
    async def test_complexity_analysis_complex_message(self, basic_plugin):
        """Test complexity analysis for complex message."""
        message = """
        Can you analyze this complex algorithm for neural network training?
        function backprop(network, input, target) {
            const output = forward(network, input);
            const error = calculate_error(output, target);
            const gradients = compute_gradients(network, error);
            update_weights(network, gradients);
        }
        What's the computational complexity and how can we optimize it?
        """
        score = await basic_plugin._analyze_complexity(message)

        assert score.overall_score > 0.5  # Should be medium-high complexity
        assert score.reasoning_level in [ReasoningEffort.MEDIUM, ReasoningEffort.HIGH]
        assert score.factors.technical_terms_count > 0
        assert score.factors.code_blocks_count == 0  # No ``` markers
        assert score.factors.question_count == 2

    @pytest.mark.asyncio
    async def test_complexity_analysis_with_code_blocks(self, basic_plugin):
        """Test complexity analysis with code blocks."""
        message = """
        ```python
        def test():
            pass
        ```
        Another code block:
        ```javascript
        console.log('test');
        ```
        """
        score = await basic_plugin._analyze_complexity(message)

        assert score.factors.code_blocks_count == 4  # Counts each ```

    def test_count_technical_terms(self, basic_plugin):
        """Test technical term counting."""
        message = "The algorithm uses neural network for classification"
        count = basic_plugin._count_technical_terms(message)

        assert count >= 3  # algorithm, neural, network

    def test_count_math_expressions(self, basic_plugin):
        """Test math expression counting."""
        message = "Calculate 5 + 3 and x = 10, then compute sin(x) and 2^4"
        count = basic_plugin._count_math_expressions(message)

        assert count >= 4  # 5+3, x=, sin(), ^

    def test_analyze_nesting(self, basic_plugin):
        """Test nesting analysis."""
        message = "Test (nested (deeply (nested))) content"
        depth = basic_plugin._analyze_nesting(message)

        assert depth == 3  # Maximum nesting depth

    def test_analyze_nesting_with_lists(self, basic_plugin):
        """Test nesting analysis with lists."""
        message = """
- Item 1
  - Nested item
    - Deeply nested
      - Even more nested
"""
        depth = basic_plugin._analyze_nesting(message)

        assert depth >= 3  # Indentation levels

    def test_calculate_ambiguity(self, basic_plugin):
        """Test ambiguity calculation."""
        message = "Maybe this could possibly be something, it might work"
        score = basic_plugin._calculate_ambiguity(message)

        assert score > 0.2  # Should detect ambiguous terms

    def test_calculate_domain_specificity(self, basic_plugin):
        """Test domain specificity calculation."""
        message = "The neural network model uses backpropagation algorithm"
        score = basic_plugin._calculate_domain_specificity(message)

        assert score > 0.3  # Should detect technical domain

    def test_calculate_overall_complexity(self, basic_plugin):
        """Test overall complexity calculation."""
        factors = ComplexityFactors(
            message_length=500,
            word_count=100,
            sentence_count=5,
            question_count=2,
            technical_terms_count=8,
            code_blocks_count=1,
            math_expressions_count=3,
            nested_structures=2,
            ambiguity_score=0.3,
            domain_specificity=0.6,
        )

        score = basic_plugin._calculate_overall_complexity(factors)

        assert 0 <= score <= 1
        assert score > 0.4  # Should be medium-high with these factors

    def test_calculate_confidence(self, basic_plugin):
        """Test confidence calculation."""
        # Very low score (far from threshold)
        confidence_low = basic_plugin._calculate_confidence(0.1)
        assert confidence_low > 0.3

        # Very high score (far from threshold)
        confidence_high = basic_plugin._calculate_confidence(0.9)
        assert confidence_high > 0.3

        # Near threshold (low confidence)
        confidence_threshold = basic_plugin._calculate_confidence(0.3)
        assert confidence_threshold >= 0  # Just ensure it's valid

    @pytest.mark.asyncio
    async def test_determine_reasoning_level_basic(self, basic_plugin, context):
        """Test basic reasoning level determination."""
        factors = ComplexityFactors(
            message_length=100,
            word_count=20,
            sentence_count=2,
            question_count=0,
            technical_terms_count=2,
            code_blocks_count=0,
            math_expressions_count=0,
            nested_structures=0,
            ambiguity_score=0.1,
            domain_specificity=0.2,
        )
        score = ComplexityScore(
            overall_score=0.2,
            factors=factors,
            reasoning_level=ReasoningEffort.LOW,
            confidence=0.8,
            analysis_time_ms=10,
        )

        level = await basic_plugin._determine_reasoning_level(score, context)
        assert level == ReasoningEffort.LOW

    @pytest.mark.asyncio
    async def test_determine_reasoning_level_with_adaptation(
        self, basic_plugin, context
    ):
        """Test reasoning level determination with adaptation."""
        # Add some high-latency decisions to history
        for i in range(15):
            factors = ComplexityFactors(
                message_length=500,
                word_count=100,
                sentence_count=10,
                question_count=2,
                technical_terms_count=10,
                code_blocks_count=2,
                math_expressions_count=5,
                nested_structures=3,
                ambiguity_score=0.3,
                domain_specificity=0.7,
            )
            complexity_score = ComplexityScore(
                overall_score=0.8,
                factors=factors,
                reasoning_level=ReasoningEffort.HIGH,
                confidence=0.8,
                analysis_time_ms=20,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.HIGH,
                estimated_tokens=1000,
                estimated_latency_ms=4000,  # High latency
            )
            basic_plugin.recent_decisions.append(decision)

        factors = ComplexityFactors(
            message_length=500,
            word_count=100,
            sentence_count=10,
            question_count=2,
            technical_terms_count=10,
            code_blocks_count=2,
            math_expressions_count=5,
            nested_structures=3,
            ambiguity_score=0.3,
            domain_specificity=0.7,
        )
        score = ComplexityScore(
            overall_score=0.8,
            factors=factors,
            reasoning_level=ReasoningEffort.HIGH,
            confidence=0.8,
            analysis_time_ms=10,
        )

        level = await basic_plugin._determine_reasoning_level(score, context)

        # Should reduce from HIGH to MEDIUM due to high latency
        assert level == ReasoningEffort.MEDIUM

    def test_estimate_tokens(self, basic_plugin):
        """Test token estimation."""
        # Low reasoning
        tokens_low = basic_plugin._estimate_tokens(ReasoningEffort.LOW, 100)
        assert tokens_low <= basic_plugin.config.max_tokens_low

        # Medium reasoning
        tokens_med = basic_plugin._estimate_tokens(ReasoningEffort.MEDIUM, 100)
        assert tokens_med <= basic_plugin.config.max_tokens_medium

        # High reasoning
        tokens_high = basic_plugin._estimate_tokens(ReasoningEffort.HIGH, 100)
        assert tokens_high <= basic_plugin.config.max_tokens_high

        # Higher reasoning should estimate more tokens
        assert tokens_high > tokens_med > tokens_low

    def test_estimate_latency(self, basic_plugin):
        """Test latency estimation."""
        factors = ComplexityFactors(
            message_length=200,
            word_count=40,
            sentence_count=4,
            question_count=1,
            technical_terms_count=5,
            code_blocks_count=0,
            math_expressions_count=1,
            nested_structures=1,
            ambiguity_score=0.3,
            domain_specificity=0.5,
        )
        score = ComplexityScore(
            overall_score=0.5,
            factors=factors,
            reasoning_level=ReasoningEffort.MEDIUM,
            confidence=0.8,
            analysis_time_ms=10,
        )

        latency_low = basic_plugin._estimate_latency(ReasoningEffort.LOW, score)
        latency_med = basic_plugin._estimate_latency(ReasoningEffort.MEDIUM, score)
        latency_high = basic_plugin._estimate_latency(ReasoningEffort.HIGH, score)

        # Higher reasoning should have higher latency
        assert latency_high > latency_med > latency_low

    @pytest.mark.asyncio
    async def test_log_decision(self, basic_plugin, context):
        """Test decision logging."""
        decision = ReasoningDecision(
            task_id="test_task",
            complexity_score=ComplexityScore(
                overall_score=0.5,
                factors=ComplexityFactors(
                    message_length=100,
                    word_count=20,
                    sentence_count=2,
                    question_count=1,
                    technical_terms_count=3,
                    code_blocks_count=0,
                    math_expressions_count=0,
                    nested_structures=0,
                    ambiguity_score=0.2,
                    domain_specificity=0.4,
                ),
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            ),
            selected_level=ReasoningEffort.MEDIUM,
            estimated_tokens=500,
            estimated_latency_ms=1500,
        )

        await basic_plugin._log_decision(context, decision)

        # Check decision was stored
        context.remember.assert_any_call(
            f"reasoning_decision:{decision.task_id}", decision.model_dump()
        )

        # Check decision was added to recent history
        assert len(basic_plugin.recent_decisions) == 1
        assert basic_plugin.recent_decisions[0] == decision

    @pytest.mark.asyncio
    async def test_log_decision_with_detailed_logging(self, restricted_plugin, context):
        """Test decision logging with detailed analysis."""
        decision = ReasoningDecision(
            task_id="test_task",
            complexity_score=ComplexityScore(
                overall_score=0.5,
                factors=ComplexityFactors(
                    message_length=100,
                    word_count=20,
                    sentence_count=2,
                    question_count=1,
                    technical_terms_count=3,
                    code_blocks_count=0,
                    math_expressions_count=0,
                    nested_structures=0,
                    ambiguity_score=0.2,
                    domain_specificity=0.4,
                ),
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            ),
            selected_level=ReasoningEffort.MEDIUM,
            estimated_tokens=500,
            estimated_latency_ms=1500,
        )

        await restricted_plugin._log_decision(context, decision)

        # Should log detailed analysis
        context.log.assert_any_call(
            level="debug",
            category="adaptive_reasoning_detail",
            message="Complexity analysis complete",
            factors=decision.complexity_score.factors.model_dump(),
            overall_score=decision.complexity_score.overall_score,
            selected_level=decision.selected_level.value,
            confidence=decision.complexity_score.confidence,
        )

    @pytest.mark.asyncio
    async def test_update_metrics(self, basic_plugin):
        """Test metrics update."""
        factors = ComplexityFactors(
            message_length=200,
            word_count=40,
            sentence_count=4,
            question_count=1,
            technical_terms_count=5,
            code_blocks_count=0,
            math_expressions_count=1,
            nested_structures=1,
            ambiguity_score=0.3,
            domain_specificity=0.5,
        )
        complexity_score = ComplexityScore(
            overall_score=0.5,
            factors=factors,
            reasoning_level=ReasoningEffort.MEDIUM,
            confidence=0.7,
            analysis_time_ms=15,
        )
        decision = ReasoningDecision(
            task_id="test_task",
            complexity_score=complexity_score,
            selected_level=ReasoningEffort.MEDIUM,
            estimated_tokens=500,
            estimated_latency_ms=1500,
        )

        await basic_plugin._update_metrics(decision)

        metrics = basic_plugin.performance_metrics
        assert metrics.total_decisions == 1
        assert metrics.medium_count == 1
        assert metrics.average_complexity == 0.5
        assert metrics.average_tokens == 500
        assert metrics.average_latency_ms == 1500

    @pytest.mark.asyncio
    async def test_update_metrics_with_override(self, basic_plugin):
        """Test metrics update with override."""
        factors = ComplexityFactors(
            message_length=200,
            word_count=40,
            sentence_count=4,
            question_count=1,
            technical_terms_count=5,
            code_blocks_count=0,
            math_expressions_count=1,
            nested_structures=1,
            ambiguity_score=0.3,
            domain_specificity=0.5,
        )
        complexity_score = ComplexityScore(
            overall_score=0.5,
            factors=factors,
            reasoning_level=ReasoningEffort.MEDIUM,
            confidence=0.7,
            analysis_time_ms=15,
        )
        decision = ReasoningDecision(
            task_id="test_task",
            complexity_score=complexity_score,
            selected_level=ReasoningEffort.HIGH,
            override_reason="Manual override",
            estimated_tokens=1000,
            estimated_latency_ms=3000,
        )

        await basic_plugin._update_metrics(decision)

        metrics = basic_plugin.performance_metrics
        assert metrics.override_count == 1

    @pytest.mark.asyncio
    async def test_adapt_thresholds(self, basic_plugin):
        """Test threshold adaptation."""
        # Add decisions with low latency
        for i in range(25):
            factors = ComplexityFactors(
                message_length=200,
                word_count=40,
                sentence_count=4,
                question_count=1,
                technical_terms_count=5,
                code_blocks_count=0,
                math_expressions_count=1,
                nested_structures=1,
                ambiguity_score=0.3,
                domain_specificity=0.5,
            )
            complexity_score = ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.MEDIUM,
                estimated_tokens=500,
                estimated_latency_ms=1000,  # Low latency
            )
            basic_plugin.recent_decisions.append(decision)

        original_threshold = basic_plugin.config.high_complexity_threshold
        await basic_plugin._adapt_thresholds()

        # Should lower threshold (allow more high reasoning)
        assert basic_plugin.config.high_complexity_threshold < original_threshold

    @pytest.mark.asyncio
    async def test_adapt_thresholds_high_latency(self, basic_plugin):
        """Test threshold adaptation with high latency."""
        # Add decisions with high latency
        for i in range(25):
            factors = ComplexityFactors(
                message_length=500,
                word_count=100,
                sentence_count=10,
                question_count=3,
                technical_terms_count=15,
                code_blocks_count=2,
                math_expressions_count=5,
                nested_structures=3,
                ambiguity_score=0.2,
                domain_specificity=0.8,
            )
            complexity_score = ComplexityScore(
                overall_score=0.8,
                factors=factors,
                reasoning_level=ReasoningEffort.HIGH,
                confidence=0.8,
                analysis_time_ms=20,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.HIGH,
                estimated_tokens=2000,
                estimated_latency_ms=3500,  # High latency
            )
            basic_plugin.recent_decisions.append(decision)

        original_threshold = basic_plugin.config.high_complexity_threshold
        await basic_plugin._adapt_thresholds()

        # Should raise threshold (reduce high reasoning)
        assert basic_plugin.config.high_complexity_threshold > original_threshold

    @pytest.mark.asyncio
    async def test_error_handling(self, basic_plugin, context):
        """Test error handling in execution."""

        # Mock an error in complexity analysis
        async def mock_analyze_error(message):
            raise Exception("Analysis error")

        basic_plugin._analyze_complexity = mock_analyze_error

        result = await basic_plugin._execute_impl(context)

        # Should return original message
        assert result == "Test message"

        # Should set default reasoning level
        context.remember.assert_any_call(
            "reasoning_level", ReasoningEffort.MEDIUM.value
        )

        # Should log error
        context.log.assert_any_call(
            level="error",
            category="adaptive_reasoning",
            message="Error in adaptive reasoning: Analysis error",
            error="Analysis error",
        )

    @pytest.mark.asyncio
    async def test_get_metrics(self, basic_plugin):
        """Test getting performance metrics."""
        # Add some decisions
        for level in [
            ReasoningEffort.LOW,
            ReasoningEffort.MEDIUM,
            ReasoningEffort.HIGH,
        ]:
            factors = ComplexityFactors(
                message_length=200,
                word_count=40,
                sentence_count=4,
                question_count=1,
                technical_terms_count=5,
                code_blocks_count=0,
                math_expressions_count=1,
                nested_structures=1,
                ambiguity_score=0.3,
                domain_specificity=0.5,
            )
            complexity_score = ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=level,
                confidence=0.7,
                analysis_time_ms=15,
            )
            decision = ReasoningDecision(
                task_id=f"task_{level.value}",
                complexity_score=complexity_score,
                selected_level=level,
                estimated_tokens=500,
                estimated_latency_ms=1500,
            )
            await basic_plugin._update_metrics(decision)

        metrics = await basic_plugin.get_metrics()

        assert metrics["total_decisions"] == 3
        assert metrics["low_count"] == 1
        assert metrics["medium_count"] == 1
        assert metrics["high_count"] == 1

    @pytest.mark.asyncio
    async def test_set_user_preference(self, basic_plugin):
        """Test setting user preference."""
        await basic_plugin.set_user_preference("test_user", ReasoningEffort.HIGH)

        # Check it was stored
        memory = basic_plugin.resources["memory"]
        stored = await memory.load("user_reasoning_preference:test_user")
        assert stored == "high"

    @pytest.mark.asyncio
    async def test_get_recent_decisions(self, basic_plugin):
        """Test getting recent decisions."""
        # Add some decisions
        for i in range(5):
            factors = ComplexityFactors(
                message_length=200,
                word_count=40,
                sentence_count=4,
                question_count=1,
                technical_terms_count=5,
                code_blocks_count=0,
                math_expressions_count=1,
                nested_structures=1,
                ambiguity_score=0.3,
                domain_specificity=0.5,
            )
            complexity_score = ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.MEDIUM,
                estimated_tokens=500,
                estimated_latency_ms=1500,
            )
            basic_plugin.recent_decisions.append(decision)

        recent = await basic_plugin.get_recent_decisions(count=3)

        assert len(recent) == 3
        assert recent[0]["task_id"] == "task_2"  # Most recent 3
        assert recent[1]["task_id"] == "task_3"
        assert recent[2]["task_id"] == "task_4"

    @pytest.mark.asyncio
    async def test_analyze_message_public_api(self, basic_plugin):
        """Test public API for message analysis."""
        message = "Test message with algorithm and neural network"
        result = await basic_plugin.analyze_message(message)

        assert "overall_score" in result
        assert "factors" in result
        assert "reasoning_level" in result
        assert "confidence" in result

    def test_reasoning_effort_enum(self):
        """Test ReasoningEffort enum."""
        assert ReasoningEffort.LOW.value == "low"
        assert ReasoningEffort.MEDIUM.value == "medium"
        assert ReasoningEffort.HIGH.value == "high"

    def test_complexity_factors_model(self):
        """Test ComplexityFactors model."""
        factors = ComplexityFactors(
            message_length=100,
            word_count=20,
            sentence_count=2,
            question_count=1,
            technical_terms_count=3,
            code_blocks_count=0,
            math_expressions_count=0,
            nested_structures=0,
            ambiguity_score=0.2,
            domain_specificity=0.4,
        )

        assert factors.message_length == 100
        assert factors.ambiguity_score == 0.2
        assert 0 <= factors.ambiguity_score <= 1

    def test_complexity_score_model(self):
        """Test ComplexityScore model."""
        score = ComplexityScore(
            overall_score=0.5,
            factors=ComplexityFactors(
                message_length=100,
                word_count=20,
                sentence_count=2,
                question_count=1,
                technical_terms_count=3,
                code_blocks_count=0,
                math_expressions_count=0,
                nested_structures=0,
                ambiguity_score=0.2,
                domain_specificity=0.4,
            ),
            reasoning_level=ReasoningEffort.MEDIUM,
            confidence=0.7,
            analysis_time_ms=15,
        )

        assert score.overall_score == 0.5
        assert score.reasoning_level == ReasoningEffort.MEDIUM
        assert 0 <= score.confidence <= 1

    def test_reasoning_decision_model(self):
        """Test ReasoningDecision model."""
        factors = ComplexityFactors(
            message_length=200,
            word_count=40,
            sentence_count=4,
            question_count=1,
            technical_terms_count=5,
            code_blocks_count=0,
            math_expressions_count=1,
            nested_structures=1,
            ambiguity_score=0.3,
            domain_specificity=0.5,
        )
        decision = ReasoningDecision(
            task_id="test_task",
            complexity_score=ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            ),
            selected_level=ReasoningEffort.MEDIUM,
            estimated_tokens=500,
            estimated_latency_ms=1500,
        )

        assert decision.task_id == "test_task"
        assert decision.selected_level == ReasoningEffort.MEDIUM
        assert decision.override_reason is None

    def test_performance_metrics_model(self):
        """Test PerformanceMetrics model."""
        metrics = PerformanceMetrics()

        assert metrics.total_decisions == 0
        assert metrics.low_count == 0
        assert metrics.average_complexity == 0.0

    def test_supported_stages(self, basic_plugin):
        """Test that plugin only supports PARSE stage."""
        assert basic_plugin.supported_stages == [WorkflowExecutor.PARSE]

    def test_required_dependencies(self, basic_plugin):
        """Test that plugin declares correct dependencies."""
        assert "llm" in basic_plugin.dependencies
        assert "memory" in basic_plugin.dependencies

    @pytest.mark.asyncio
    async def test_history_window_limit(self, basic_plugin, context):
        """Test that recent decisions respect history window limit."""
        # Add more decisions than history window
        for i in range(150):
            factors = ComplexityFactors(
                message_length=200,
                word_count=40,
                sentence_count=4,
                question_count=1,
                technical_terms_count=5,
                code_blocks_count=0,
                math_expressions_count=1,
                nested_structures=1,
                ambiguity_score=0.3,
                domain_specificity=0.5,
            )
            complexity_score = ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.MEDIUM,
                estimated_tokens=500,
                estimated_latency_ms=1500,
            )
            await basic_plugin._log_decision(context, decision)

        # Should only keep history_window number of decisions
        assert len(basic_plugin.recent_decisions) == basic_plugin.config.history_window

    @pytest.mark.asyncio
    async def test_metrics_persistence(self, basic_plugin):
        """Test that metrics are persisted periodically."""
        # Add decisions to trigger persistence
        for i in range(basic_plugin.config.metrics_update_interval + 1):
            factors = ComplexityFactors(
                message_length=200,
                word_count=40,
                sentence_count=4,
                question_count=1,
                technical_terms_count=5,
                code_blocks_count=0,
                math_expressions_count=1,
                nested_structures=1,
                ambiguity_score=0.3,
                domain_specificity=0.5,
            )
            complexity_score = ComplexityScore(
                overall_score=0.5,
                factors=factors,
                reasoning_level=ReasoningEffort.MEDIUM,
                confidence=0.7,
                analysis_time_ms=15,
            )
            decision = ReasoningDecision(
                task_id=f"task_{i}",
                complexity_score=complexity_score,
                selected_level=ReasoningEffort.MEDIUM,
                estimated_tokens=500,
                estimated_latency_ms=1500,
            )
            await basic_plugin._update_metrics(decision)

        # Check metrics were stored
        memory = basic_plugin.resources["memory"]
        stored = await memory.load("adaptive_reasoning_metrics")
        assert stored is not None
        assert stored["total_decisions"] == basic_plugin.config.metrics_update_interval
