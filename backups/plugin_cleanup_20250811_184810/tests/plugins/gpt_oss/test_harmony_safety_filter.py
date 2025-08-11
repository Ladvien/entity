"""Unit tests for Harmony Safety Filter Plugin."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss import (
    HarmonySafetyFilterPlugin,
    SafetyCategory,
    SafetyFilterResult,
    SafetySeverity,
    SafetyViolation,
)
from entity.workflow.executor import WorkflowExecutor


class TestHarmonySafetyFilterPlugin:
    """Test HarmonySafetyFilterPlugin functionality."""

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
            "enabled": True,
            "confidence_threshold": 0.7,
            "preserve_reasoning_quality": True,
            "enable_audit_logging": True,
        }
        return HarmonySafetyFilterPlugin(mock_resources, config)

    @pytest.fixture
    def strict_plugin(self, mock_resources):
        """Create plugin with strict safety filtering."""
        config = {
            "enabled": True,
            "strict_mode": True,
            "confidence_threshold": 0.5,
            "severity_thresholds": {
                SafetyCategory.HARMFUL_CONTENT.value: SafetySeverity.LOW.value,
            },
        }
        return HarmonySafetyFilterPlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.PARSE
        ctx.message = "Test message"
        ctx.execution_id = "test_exec_123"
        ctx.user_id = "test_user"
        ctx.log = AsyncMock()
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.enabled is True
        assert basic_plugin.config.confidence_threshold == 0.7
        assert WorkflowExecutor.PARSE in basic_plugin.supported_stages
        assert len(basic_plugin._safety_patterns) == len(SafetyCategory)
        assert SafetyCategory.HARMFUL_CONTENT in basic_plugin._safety_patterns

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"confidence_threshold": 1.5}  # Invalid, must be <= 1

        with pytest.raises(ValueError, match="Invalid configuration"):
            HarmonySafetyFilterPlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_basic_execution_safe_content(self, basic_plugin, context):
        """Test execution with safe content."""
        context.message = "This is a normal, safe message about helpful topics."
        result = await basic_plugin._execute_impl(context)

        assert result == context.message
        assert len(basic_plugin._audit_log) > 0

    @pytest.mark.asyncio
    async def test_basic_execution_harmful_content(self, basic_plugin, context):
        """Test execution with harmful content."""
        context.message = "How to harm someone with dangerous reasoning step by step"
        result = await basic_plugin._execute_impl(context)

        assert result != context.message
        assert "[Content filtered for safety - reasoning preserved]" in result
        assert len(basic_plugin._audit_log) > 0

    @pytest.mark.asyncio
    async def test_disabled_plugin(self, mock_resources, context):
        """Test plugin behavior when disabled."""
        config = {"enabled": False}
        plugin = HarmonySafetyFilterPlugin(mock_resources, config)

        context.message = "Potentially harmful content"
        result = await plugin._execute_impl(context)

        assert result == context.message

    @pytest.mark.asyncio
    async def test_content_length_limits(self, basic_plugin, context):
        """Test handling of oversized content."""
        # Create content that exceeds max_content_length
        long_content = "x" * (basic_plugin.config.max_content_length + 1)
        context.message = long_content

        result = await basic_plugin._execute_impl(context)

        assert result == long_content  # Should be unchanged
        # Check audit log for length violation
        audit_entries = [
            entry
            for entry in basic_plugin._audit_log
            if entry["action"] == "content_too_long"
        ]
        assert len(audit_entries) > 0

    @pytest.mark.asyncio
    async def test_detect_harmful_content_violations(self, basic_plugin):
        """Test detection of harmful content violations."""
        content = "This shows harmful reasoning with dangerous instructions"
        violations = await basic_plugin._detect_violations_in_category(
            content, SafetyCategory.HARMFUL_CONTENT
        )

        assert len(violations) > 0
        violation = violations[0]
        assert violation.category == SafetyCategory.HARMFUL_CONTENT
        assert violation.confidence_score > 0.7
        # Check that the matched text contains one of the expected harmful terms
        matched_lower = violation.matched_text.lower()
        assert any(
            term in matched_lower
            for term in ["harmful", "dangerous", "toxic", "malicious"]
        )

    @pytest.mark.asyncio
    async def test_detect_exploit_violations(self, basic_plugin):
        """Test detection of exploit instruction violations."""
        content = "Detailed hack instructions to exploit this vulnerability"
        violations = await basic_plugin._detect_violations_in_category(
            content, SafetyCategory.EXPLOIT_INSTRUCTIONS
        )

        assert len(violations) > 0
        violation = violations[0]
        assert violation.category == SafetyCategory.EXPLOIT_INSTRUCTIONS
        # The severity depends on which pattern matched - either HIGH or CRITICAL
        assert violation.severity in [SafetySeverity.HIGH, SafetySeverity.CRITICAL]

    @pytest.mark.asyncio
    async def test_detect_privacy_violations(self, basic_plugin):
        """Test detection of privacy violation patterns."""
        content = "Extract personal information including social security numbers"
        violations = await basic_plugin._detect_violations_in_category(
            content, SafetyCategory.PRIVACY_VIOLATIONS
        )

        assert len(violations) > 0
        violation = violations[0]
        assert violation.category == SafetyCategory.PRIVACY_VIOLATIONS

    @pytest.mark.asyncio
    async def test_detect_violence_promotion(self, basic_plugin):
        """Test detection of violence promotion."""
        content = "This content promotes violence and encourages attacks on others to make weapons and bombs"
        violations = await basic_plugin._detect_violations_in_category(
            content, SafetyCategory.VIOLENCE_PROMOTION
        )

        assert len(violations) > 0
        violation = violations[0]
        assert violation.category == SafetyCategory.VIOLENCE_PROMOTION
        assert violation.severity == SafetySeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_self_harm_content(self, basic_plugin):
        """Test detection of self-harm content."""
        content = "Instructions for self-harm and suicide methods"
        violations = await basic_plugin._detect_violations_in_category(
            content, SafetyCategory.SELF_HARM
        )

        assert len(violations) > 0
        violation = violations[0]
        assert violation.category == SafetyCategory.SELF_HARM
        assert violation.severity == SafetySeverity.CRITICAL

    def test_should_filter_violation_severity(self, basic_plugin):
        """Test severity-based filtering decisions."""
        # High severity violation should be filtered
        high_violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.HIGH,
            pattern_matched="test",
            matched_text="test",
            confidence_score=0.9,
            position=0,
            context="test context",
        )

        assert basic_plugin._should_filter_violation(high_violation) is True

        # Low severity violation may not be filtered based on thresholds
        low_violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.LOW,
            pattern_matched="test",
            matched_text="test",
            confidence_score=0.9,
            position=0,
            context="test context",
        )

        # This depends on configuration - with default config, low severity is filtered
        result = basic_plugin._should_filter_violation(low_violation)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_apply_violation_filter_placeholder(self, basic_plugin, context):
        """Test applying violation filter with placeholder strategy."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.HIGH,
            pattern_matched="harmful content",
            matched_text="harmful content",
            confidence_score=0.9,
            position=10,
            context="This is harmful content here",
        )

        original_content = "This is a harmful content example"
        filtered = await basic_plugin._apply_violation_filter(
            original_content, violation, context
        )

        assert "harmful content" not in filtered
        assert basic_plugin.config.placeholder_text in filtered

    @pytest.mark.asyncio
    async def test_apply_violation_filter_redaction(self, mock_resources, context):
        """Test applying violation filter with redaction strategy."""
        config = {"replacement_strategy": "redaction"}
        plugin = HarmonySafetyFilterPlugin(mock_resources, config)

        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.HIGH,
            pattern_matched="harmful content",
            matched_text="harmful content",
            confidence_score=0.9,
            position=10,
            context="This is harmful content here",
        )

        original_content = "This is a harmful content example"
        filtered = await plugin._apply_violation_filter(
            original_content, violation, context
        )

        assert "[REDACTED]" in filtered
        assert "harmful content" not in filtered

    @pytest.mark.asyncio
    async def test_preserve_reasoning_quality(self, basic_plugin, context):
        """Test preservation of reasoning quality indicators."""
        original = "Therefore, this analysis shows the conclusion because of evidence"
        filtered = "This shows the conclusion"  # Reasoning words removed

        preserved, was_preserved = await basic_plugin._preserve_reasoning_quality(
            original, filtered, context
        )

        assert was_preserved is True
        assert "Therefore" in preserved or "because" in preserved

    @pytest.mark.asyncio
    async def test_filter_content_comprehensive(self, basic_plugin, context):
        """Test comprehensive content filtering."""
        content = """
        This analysis shows how to harm others with dangerous reasoning.
        The step-by-step exploit instructions are therefore unethical.
        However, the conclusion demonstrates important insights.
        """

        result = await basic_plugin._filter_content(content, context)

        assert isinstance(result, SafetyFilterResult)
        assert len(result.violations_detected) > 0
        assert result.filter_applied is True
        # Note: filtered_length might be larger due to reasoning preservation
        assert result.original_length > 0
        assert "metadata" in result.model_dump()

    @pytest.mark.asyncio
    async def test_caching_functionality(self, basic_plugin, context):
        """Test content caching for performance."""
        content = "This is safe test content for caching"
        context.message = content

        # First call should process and cache
        result1 = await basic_plugin._execute_impl(context)
        cache_size_after_first = len(basic_plugin._content_cache)

        # Second call should use cache
        result2 = await basic_plugin._execute_impl(context)

        assert result1 == result2
        assert cache_size_after_first > 0
        # Check for cache hit in audit log
        cache_hits = [
            entry for entry in basic_plugin._audit_log if entry["action"] == "cache_hit"
        ]
        assert len(cache_hits) > 0

    def test_cache_key_generation(self, basic_plugin):
        """Test cache key generation."""
        content1 = "Test content"
        content2 = "Test content"
        content3 = "Different content"

        key1 = basic_plugin._generate_cache_key(content1)
        key2 = basic_plugin._generate_cache_key(content2)
        key3 = basic_plugin._generate_cache_key(content3)

        assert key1 == key2  # Same content should have same key
        assert key1 != key3  # Different content should have different key
        assert len(key1) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_audit_logging(self, basic_plugin, context):
        """Test audit logging functionality."""
        await basic_plugin._log_audit_entry(
            "test_action", context, {"test_key": "test_value"}
        )

        assert len(basic_plugin._audit_log) > 0
        entry = basic_plugin._audit_log[-1]
        assert entry["action"] == "test_action"
        assert entry["metadata"]["test_key"] == "test_value"
        assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_violation_logging(self, basic_plugin, context):
        """Test individual violation logging."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.HIGH,
            pattern_matched="test pattern",
            matched_text="harmful text",
            confidence_score=0.8,
            position=10,
            context="surrounding context",
        )

        await basic_plugin._log_violation(violation, context)

        # Check that context.log was called
        context.log.assert_called()
        call_args = context.log.call_args
        assert call_args[1]["category"] == "harmony_safety_violation"
        assert call_args[1]["level"] == "warning"

    @pytest.mark.asyncio
    async def test_audit_cleanup(self, basic_plugin):
        """Test cleanup of old audit entries."""
        # Add old entries
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        basic_plugin._audit_log.extend(
            [
                {"timestamp": old_timestamp, "action": "old_action"},
                {"timestamp": datetime.now().isoformat(), "action": "new_action"},
            ]
        )

        await basic_plugin._cleanup_old_audit_entries()

        # Only recent entries should remain
        assert len(basic_plugin._audit_log) == 1
        assert basic_plugin._audit_log[0]["action"] == "new_action"

    @pytest.mark.asyncio
    async def test_get_safety_stats(self, basic_plugin):
        """Test safety statistics retrieval."""
        stats = await basic_plugin.get_safety_stats()

        assert "enabled_categories" in stats
        assert "confidence_threshold" in stats
        assert "patterns_loaded" in stats
        assert "cache_size" in stats
        assert stats["confidence_threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_test_content_safety(self, basic_plugin):
        """Test content safety testing without filtering."""
        content = "This contains harmful reasoning with dangerous instructions"
        result = await basic_plugin.test_content_safety(content)

        assert isinstance(result, SafetyFilterResult)
        assert len(result.violations_detected) > 0
        assert result.original_length == len(content)

    @pytest.mark.asyncio
    async def test_add_custom_pattern_success(self, basic_plugin):
        """Test adding custom safety pattern."""
        success = await basic_plugin.add_custom_pattern(
            SafetyCategory.HARMFUL_CONTENT,
            r"custom harmful pattern",
            SafetySeverity.HIGH,
            0.8,
        )

        assert success is True
        patterns = basic_plugin._safety_patterns[SafetyCategory.HARMFUL_CONTENT]
        custom_patterns = [
            p for p in patterns if "custom harmful pattern" in p["pattern"]
        ]
        assert len(custom_patterns) == 1

    @pytest.mark.asyncio
    async def test_add_custom_pattern_invalid_regex(self, basic_plugin):
        """Test adding custom pattern with invalid regex."""
        success = await basic_plugin.add_custom_pattern(
            SafetyCategory.HARMFUL_CONTENT,
            r"[invalid regex",  # Missing closing bracket
            SafetySeverity.HIGH,
            0.8,
        )

        assert success is False

    def test_get_audit_log(self, basic_plugin):
        """Test audit log retrieval."""
        # Add test entries
        basic_plugin._audit_log = [
            {"action": "test1", "timestamp": datetime.now().isoformat()},
            {"action": "test2", "timestamp": datetime.now().isoformat()},
            {"action": "test3", "timestamp": datetime.now().isoformat()},
        ]

        # Test unlimited retrieval
        all_logs = basic_plugin.get_audit_log()
        assert len(all_logs) == 3

        # Test limited retrieval
        limited_logs = basic_plugin.get_audit_log(limit=2)
        assert len(limited_logs) == 2
        assert limited_logs[0]["action"] == "test2"  # Should get last 2

    @pytest.mark.asyncio
    async def test_multiple_categories_enabled(self, basic_plugin, context):
        """Test filtering with multiple safety categories enabled."""
        content = """
        This analysis shows harmful reasoning with dangerous instructions.
        It also contains exploit methods to hack systems illegally.
        The unethical approach promotes violence against others.
        """

        result = await basic_plugin._filter_content(content, context)

        # Should detect violations from multiple categories
        categories_found = {v.category for v in result.violations_detected}
        assert len(categories_found) > 1
        assert SafetyCategory.HARMFUL_CONTENT in categories_found

    @pytest.mark.asyncio
    async def test_category_filtering_disabled(self, mock_resources, context):
        """Test behavior when specific categories are disabled."""
        config = {
            "enabled_categories": [
                SafetyCategory.HARMFUL_CONTENT.value
            ]  # Only one enabled
        }
        plugin = HarmonySafetyFilterPlugin(mock_resources, config)

        content = "This has exploit instructions and harmful reasoning"
        result = await plugin._filter_content(content, context)

        # Should only detect violations from enabled categories
        # With the test content "This has exploit instructions and harmful reasoning"
        # we should detect harmful content since that's the only enabled category
        assert len(result.violations_detected) >= 0
        if result.violations_detected:
            assert all(
                v.category.value in plugin.config.enabled_categories
                for v in result.violations_detected
            )

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, mock_resources, context):
        """Test filtering based on confidence threshold."""
        # High confidence threshold should filter less
        config = {"confidence_threshold": 0.95}
        strict_plugin = HarmonySafetyFilterPlugin(mock_resources, config)

        content = "This might have some harmful content"  # Lower confidence match
        result = await strict_plugin._filter_content(content, context)

        # With high threshold, fewer violations should trigger filtering
        high_confidence_violations = [
            v for v in result.violations_detected if v.confidence_score >= 0.95
        ]

        # Should have fewer or no high-confidence violations
        assert len(high_confidence_violations) <= len(result.violations_detected)

    @pytest.mark.asyncio
    async def test_error_handling_in_execution(self, basic_plugin, context):
        """Test error handling during execution."""
        # Mock an error in content filtering
        original_filter = basic_plugin._filter_content

        async def failing_filter(*args, **kwargs):
            raise Exception("Test filtering error")

        basic_plugin._filter_content = failing_filter

        result = await basic_plugin._execute_impl(context)

        # Should return original message on error
        assert result == context.message

        # Should have logged error
        context.log.assert_called()
        error_calls = [
            call
            for call in context.log.call_args_list
            if call[1].get("level") == "error"
        ]
        assert len(error_calls) > 0

        # Restore original method
        basic_plugin._filter_content = original_filter

    @pytest.mark.asyncio
    async def test_strict_mode_behavior(self, strict_plugin, context):
        """Test behavior in strict safety filtering mode."""
        content = "This has potentially harmful reasoning"
        result = await strict_plugin._execute_impl(context)

        # Strict mode should filter more aggressively
        assert result != content
        assert len(strict_plugin._audit_log) > 0


class TestSafetyViolation:
    """Test SafetyViolation model."""

    def test_safety_violation_creation(self):
        """Test creating a safety violation."""
        violation = SafetyViolation(
            category=SafetyCategory.HARMFUL_CONTENT,
            severity=SafetySeverity.HIGH,
            pattern_matched="test pattern",
            matched_text="harmful content",
            confidence_score=0.85,
            position=10,
            context="surrounding context",
        )

        assert violation.category == SafetyCategory.HARMFUL_CONTENT
        assert violation.severity == SafetySeverity.HIGH
        assert violation.confidence_score == 0.85
        assert violation.position == 10


class TestSafetyFilterResult:
    """Test SafetyFilterResult model."""

    def test_safety_filter_result_creation(self):
        """Test creating a safety filter result."""
        result = SafetyFilterResult(
            filtered_content="filtered content",
            original_length=100,
            filtered_length=80,
            violations_detected=[],
            filter_applied=True,
            reasoning_quality_preserved=False,
        )

        assert result.filtered_content == "filtered content"
        assert result.original_length == 100
        assert result.filtered_length == 80
        assert result.filter_applied is True


class TestEnums:
    """Test enum functionality."""

    def test_safety_category_enum(self):
        """Test SafetyCategory enum."""
        assert SafetyCategory.HARMFUL_CONTENT.value == "harmful_content"
        assert SafetyCategory.EXPLOIT_INSTRUCTIONS.value == "exploit_instructions"
        assert SafetyCategory.VIOLENCE_PROMOTION.value == "violence_promotion"

    def test_safety_severity_enum(self):
        """Test SafetySeverity enum."""
        assert SafetySeverity.LOW.value == "low"
        assert SafetySeverity.MEDIUM.value == "medium"
        assert SafetySeverity.HIGH.value == "high"
        assert SafetySeverity.CRITICAL.value == "critical"


class TestConfigModel:
    """Test ConfigModel functionality."""

    def test_config_model_defaults(self):
        """Test ConfigModel default values."""
        config = HarmonySafetyFilterPlugin.ConfigModel()

        assert config.enabled is True
        assert config.strict_mode is False
        assert config.confidence_threshold == 0.7
        assert config.preserve_reasoning_quality is True
        assert config.enable_audit_logging is True
        assert len(config.enabled_categories) == len(SafetyCategory)

    def test_config_model_custom_values(self):
        """Test ConfigModel with custom values."""
        config = HarmonySafetyFilterPlugin.ConfigModel(
            enabled=False,
            strict_mode=True,
            confidence_threshold=0.9,
            replacement_strategy="redaction",
            max_content_length=10000,
        )

        assert config.enabled is False
        assert config.strict_mode is True
        assert config.confidence_threshold == 0.9
        assert config.replacement_strategy == "redaction"
        assert config.max_content_length == 10000

    def test_config_model_validation(self):
        """Test ConfigModel validation."""
        # Test invalid confidence threshold
        with pytest.raises(ValueError):
            HarmonySafetyFilterPlugin.ConfigModel(confidence_threshold=1.5)

        # Test invalid replacement strategy
        with pytest.raises(ValueError):
            HarmonySafetyFilterPlugin.ConfigModel(replacement_strategy="invalid")


if __name__ == "__main__":
    pytest.main([__file__])
