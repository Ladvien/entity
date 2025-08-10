"""Tests for error analysis and debugging utilities."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from entity.core.error_analysis import ErrorAnalyzer, ErrorPattern, RecoveryStrategy
from entity.core.errors import ErrorCategory, ErrorContext, ErrorSeverity, PipelineError


class TestErrorAnalyzer:
    """Test ErrorAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create fresh ErrorAnalyzer for testing."""
        return ErrorAnalyzer()

    @pytest.fixture
    def sample_error(self):
        """Create sample pipeline error."""
        context = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=datetime.now(),
            stage="test_stage",
            plugin="test_plugin",
            plugin_stack=["plugin1", "plugin2"],
            execution_context={"operation": "test", "input_size": 100},
        )

        original_error = ValueError("Invalid input format")

        return PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=context,
            original_error=original_error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
        )

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.error_history == []
        assert analyzer.patterns == {}
        assert len(analyzer.recovery_strategies) > 0
        assert analyzer.pattern_threshold == 3

    def test_record_error_single(self, analyzer, sample_error):
        """Test recording single error."""
        analyzer.record_error(sample_error)

        assert len(analyzer.error_history) == 1
        assert analyzer.error_history[0] == sample_error
        assert len(analyzer.patterns) == 1

        # Check pattern creation
        pattern_key = list(analyzer.patterns.keys())[0]
        pattern = analyzer.patterns[pattern_key]
        assert pattern.occurrences == 1
        assert pattern.error_category == ErrorCategory.VALIDATION
        assert "test_stage" in pattern.affected_stages
        assert "test_plugin" in pattern.affected_plugins

    def test_record_error_pattern_detection(self, analyzer):
        """Test error pattern detection with multiple similar errors."""
        # Create similar errors
        for i in range(5):
            context = ErrorContext(
                request_id=str(uuid.uuid4()),
                user_id=f"user_{i}",
                timestamp=datetime.now(),
                stage="test_stage",
                plugin="test_plugin",
                execution_context={"common_key": "common_value"},
            )

            error = PipelineError(
                stage="test_stage",
                plugin="test_plugin",
                context=context,
                original_error=ValueError("Invalid input format"),
                category=ErrorCategory.VALIDATION,
            )

            analyzer.record_error(error)

        # Should detect pattern
        assert len(analyzer.patterns) == 1
        pattern = list(analyzer.patterns.values())[0]
        assert pattern.occurrences == 5
        assert (
            len(pattern.suggested_fixes) > 0
        )  # Suggestions generated for patterns above threshold

    def test_error_signature_generation(self, analyzer):
        """Test error signature generation."""
        context = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=datetime.now(),
            stage="validation_stage",
        )

        error1 = PipelineError(
            stage="validation_stage",
            plugin="validator",
            context=context,
            original_error=ValueError("Invalid input"),
            category=ErrorCategory.VALIDATION,
        )

        error2 = PipelineError(
            stage="validation_stage",
            plugin="validator",
            context=context,
            original_error=ValueError(
                "Invalid format"
            ),  # Similar but different message
            category=ErrorCategory.VALIDATION,
        )

        sig1 = analyzer._generate_error_signature(error1)
        sig2 = analyzer._generate_error_signature(error2)

        # Should generate similar signatures for similar errors
        assert sig1 == sig2  # Both are validation errors with ValueError

    def test_get_error_patterns(self, analyzer, sample_error):
        """Test error pattern retrieval."""
        # Record errors
        for _ in range(3):
            analyzer.record_error(sample_error)

        # Test with different thresholds
        patterns_all = analyzer.get_error_patterns(min_occurrences=1)
        patterns_threshold = analyzer.get_error_patterns(min_occurrences=3)
        patterns_high = analyzer.get_error_patterns(min_occurrences=5)

        assert len(patterns_all) == 1
        assert len(patterns_threshold) == 1
        assert len(patterns_high) == 0

    def test_get_recovery_suggestions(self, analyzer, sample_error):
        """Test recovery strategy suggestions."""
        suggestions = analyzer.get_recovery_suggestions(sample_error)

        # Should get suggestions for validation errors
        assert len(suggestions) > 0

        # Should be sorted by success rate
        success_rates = [s.success_rate for s in suggestions]
        assert success_rates == sorted(success_rates, reverse=True)

        # Check that suggestions are relevant to validation category
        for suggestion in suggestions:
            assert ErrorCategory.VALIDATION in suggestion.applicable_categories

    def test_analyze_recent_errors_no_errors(self, analyzer):
        """Test recent error analysis with no errors."""
        result = analyzer.analyze_recent_errors(timedelta(hours=1))

        assert result["status"] == "no_recent_errors"
        assert result["window_hours"] == 1.0

    def test_analyze_recent_errors_with_data(self, analyzer):
        """Test recent error analysis with error data."""
        # Create errors with different categories and stages
        errors_data = [
            (ErrorCategory.VALIDATION, "input_stage", "validator"),
            (ErrorCategory.NETWORK, "processing_stage", "processor"),
            (ErrorCategory.PLUGIN, "output_stage", "formatter"),
            (
                ErrorCategory.VALIDATION,
                "input_stage",
                "validator",
            ),  # Duplicate for pattern
        ]

        for category, stage, plugin in errors_data:
            context = ErrorContext(
                request_id=str(uuid.uuid4()),
                user_id="test_user",
                timestamp=datetime.now(),
                stage=stage,
                plugin=plugin,
            )

            error = PipelineError(
                stage=stage,
                plugin=plugin,
                context=context,
                original_error=RuntimeError("Test error"),
                category=category,
            )

            analyzer.record_error(error)

        result = analyzer.analyze_recent_errors(timedelta(hours=1))

        assert result["status"] == "analysis_complete"
        assert result["total_errors"] == 4
        assert result["by_category"]["validation"] == 2
        assert result["by_category"]["network"] == 1
        assert result["by_category"]["plugin"] == 1
        assert result["by_stage"]["input_stage"] == 2
        assert result["by_plugin"]["validator"] == 2
        assert len(result["recommendations"]) > 0

    def test_generate_debug_report(self, analyzer):
        """Test debug report generation."""
        request_id = str(uuid.uuid4())

        # Test with no errors
        report = analyzer.generate_debug_report(request_id)
        assert f"No errors found for request ID: {request_id}" in report

        # Create error with specific request ID
        context = ErrorContext(
            request_id=request_id,
            user_id="debug_user",
            timestamp=datetime.now(),
            stage="debug_stage",
            plugin="debug_plugin",
            plugin_stack=["plugin1", "debug_plugin"],
        )

        error = PipelineError(
            stage="debug_stage",
            plugin="debug_plugin",
            context=context,
            original_error=RuntimeError("Debug test error"),
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PLUGIN,
        )

        analyzer.record_error(error)

        # Generate report
        report = analyzer.generate_debug_report(request_id)

        assert f"Debug Report for Request ID: {request_id}" in report
        assert "Total Errors: 1" in report
        assert "Stage: debug_stage" in report
        assert "Plugin: debug_plugin" in report
        assert "Severity: high" in report
        assert "Plugin Stack: plugin1 -> debug_plugin" in report
        assert "Recovery Suggestions:" in report

    def test_common_context_tracking(self, analyzer):
        """Test common context tracking in patterns."""
        # Create errors with some common and some different contexts
        common_context = {"common_key": "common_value", "variable_key": "value1"}
        different_context = {"common_key": "common_value", "variable_key": "value2"}

        context1 = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="user1",
            timestamp=datetime.now(),
            stage="test_stage",
            execution_context=common_context,
        )

        context2 = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="user2",
            timestamp=datetime.now(),
            stage="test_stage",
            execution_context=different_context,
        )

        error1 = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=context1,
            original_error=ValueError("Test error"),
            category=ErrorCategory.VALIDATION,
        )

        error2 = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=context2,
            original_error=ValueError("Test error"),
            category=ErrorCategory.VALIDATION,
        )

        analyzer.record_error(error1)
        analyzer.record_error(error2)

        # Check that only common contexts are preserved
        pattern = list(analyzer.patterns.values())[0]
        assert "common_key" in pattern.common_contexts
        assert pattern.common_contexts["common_key"] == "common_value"
        assert (
            "variable_key" not in pattern.common_contexts
        )  # Should be removed due to difference

    def test_fix_suggestions_generation(self, analyzer):
        """Test automated fix suggestion generation."""
        # Test validation category suggestions
        _ = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=datetime.now(),
            stage="input_stage",
        )

        pattern = ErrorPattern(
            signature="test_signature",
            occurrences=5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            error_category=ErrorCategory.VALIDATION,
            affected_stages={"input_stage"},
            affected_plugins=set(),
            common_contexts={},
            suggested_fixes=[],
        )

        suggestions = analyzer._generate_fix_suggestions(pattern)

        assert len(suggestions) > 0
        validation_suggestions = [
            "Add input validation before processing",
            "Implement schema validation for data structures",
            "Add type checking for function parameters",
        ]

        for suggestion in validation_suggestions:
            assert suggestion in suggestions


class TestRecoveryStrategies:
    """Test recovery strategy functionality."""

    def test_recovery_strategy_creation(self):
        """Test RecoveryStrategy creation."""
        strategy = RecoveryStrategy(
            name="test_strategy",
            description="Test recovery strategy",
            applicable_categories={ErrorCategory.NETWORK},
            success_rate=0.8,
            implementation_notes="Test implementation",
        )

        assert strategy.name == "test_strategy"
        assert strategy.success_rate == 0.8
        assert ErrorCategory.NETWORK in strategy.applicable_categories

    def test_built_in_strategies(self):
        """Test that built-in recovery strategies are properly configured."""
        analyzer = ErrorAnalyzer()
        strategies = analyzer.recovery_strategies

        assert len(strategies) > 0

        # Check that strategies have required fields
        for strategy in strategies:
            assert strategy.name
            assert strategy.description
            assert len(strategy.applicable_categories) > 0
            assert 0 <= strategy.success_rate <= 1
            assert strategy.implementation_notes


class TestErrorPatterns:
    """Test error pattern detection and analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create fresh ErrorAnalyzer for testing."""
        return ErrorAnalyzer()

    def test_error_pattern_creation(self):
        """Test ErrorPattern creation."""
        now = datetime.now()
        pattern = ErrorPattern(
            signature="test:pattern",
            occurrences=5,
            first_seen=now,
            last_seen=now,
            error_category=ErrorCategory.PLUGIN,
            affected_stages={"stage1", "stage2"},
            affected_plugins={"plugin1"},
            common_contexts={"key": "value"},
            suggested_fixes=["Fix suggestion"],
        )

        assert pattern.signature == "test:pattern"
        assert pattern.occurrences == 5
        assert pattern.error_category == ErrorCategory.PLUGIN
        assert len(pattern.affected_stages) == 2
        assert "Fix suggestion" in pattern.suggested_fixes

    @patch("entity.core.error_analysis.datetime")
    def test_pattern_time_tracking(self, mock_datetime, analyzer):
        """Test that patterns track first and last seen times correctly."""
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        end_time = datetime(2023, 1, 1, 11, 0, 0)

        # First error
        mock_datetime.now.return_value = start_time

        context1 = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=start_time,
            stage="test_stage",
        )

        error1 = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=context1,
            original_error=ValueError("Test error"),
            category=ErrorCategory.VALIDATION,
        )

        analyzer.record_error(error1)

        # Second similar error later
        mock_datetime.now.return_value = end_time

        context2 = ErrorContext(
            request_id=str(uuid.uuid4()),
            user_id="test_user",
            timestamp=end_time,
            stage="test_stage",
        )

        error2 = PipelineError(
            stage="test_stage",
            plugin="test_plugin",
            context=context2,
            original_error=ValueError("Test error"),
            category=ErrorCategory.VALIDATION,
        )

        analyzer.record_error(error2)

        # Check timing
        pattern = list(analyzer.patterns.values())[0]
        assert pattern.first_seen == start_time
        assert pattern.last_seen == end_time
        assert pattern.occurrences == 2
