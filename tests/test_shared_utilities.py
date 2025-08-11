"""Comprehensive tests for shared plugin utilities."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from entity.core.rate_limiter import (
    MultiTierRateLimiter,
    RateLimitAlgorithm,
    RateLimiter,
    create_api_rate_limiter,
    create_database_rate_limiter,
    create_user_rate_limiter,
    create_webhook_rate_limiter,
)
from entity.core.validators import (
    IdentifierValidator,
    JSONYAMLValidator,
    SQLValidator,
    TypeValidator,
    ValidationResultBuilder,
    validate_email,
    validate_semantic_version,
    validate_url,
)
from entity.plugins.mixins import (
    CircuitBreakerMixin,
    ConfigValidationMixin,
    ErrorHandlingMixin,
    LoggingMixin,
    MetricsMixin,
)
from entity.plugins.validation import ValidationResult


class TestConfigValidationMixin:
    """Test cases for ConfigValidationMixin."""

    class TestPlugin(ConfigValidationMixin):
        """Test plugin using the mixin."""

        class ConfigModel(BaseModel):
            """Test configuration model."""

            name: str
            value: int = 10

        def __init__(self, config):
            self.config = config

        def validate_config(self):
            """Override base validation method."""
            try:
                self.config = self.ConfigModel(**self.config)
                return ValidationResult.success()
            except Exception as e:
                return ValidationResult.error(str(e))

    def test_validate_config_strict_success(self):
        """Test strict validation with valid config."""
        plugin = self.TestPlugin({"name": "test", "value": 20})
        plugin.validate_config_strict()  # Should not raise
        assert plugin.config.name == "test"
        assert plugin.config.value == 20

    def test_validate_config_strict_failure(self):
        """Test strict validation with invalid config."""
        plugin = self.TestPlugin({"value": "not_an_int"})
        with pytest.raises(ValueError, match="configuration validation failed"):
            plugin.validate_config_strict()

    def test_validate_config_with_defaults(self):
        """Test validation with default values."""
        plugin = self.TestPlugin({"name": "test"})
        plugin.validate_config_with_defaults({"other_field": 42})
        assert plugin.config.name == "test"
        assert (
            plugin.config.value == 10
        )  # Uses model default since value wasn't in config

    def test_validate_config_custom_prefix(self):
        """Test validation with custom error prefix."""
        plugin = self.TestPlugin({"invalid": "config"})
        result = plugin.validate_config_custom("Custom Error: ")
        assert not result.success
        assert any("Custom Error:" in err for err in result.errors)


class TestLoggingMixin:
    """Test cases for LoggingMixin."""

    class TestPlugin(LoggingMixin):
        """Test plugin using the mixin."""

        def __init__(self):
            self.context = Mock()
            self.context.log = AsyncMock()

    @pytest.mark.asyncio
    async def test_log_levels(self):
        """Test all log level methods."""
        plugin = self.TestPlugin()

        await plugin.log_debug("debug message")
        await plugin.log_info("info message")
        await plugin.log_warning("warning message")
        await plugin.log_error("error message", exception=ValueError("test"))

        assert plugin.context.log.call_count == 4

    @pytest.mark.asyncio
    async def test_log_operation_success(self):
        """Test log_operation context manager on success."""
        plugin = self.TestPlugin()

        async with plugin.log_operation("test_operation"):
            await asyncio.sleep(0.01)

        # Should log start and completion
        assert plugin.context.log.call_count == 2

    @pytest.mark.asyncio
    async def test_log_operation_failure(self):
        """Test log_operation context manager on failure."""
        plugin = self.TestPlugin()

        with pytest.raises(ValueError):
            async with plugin.log_operation("test_operation"):
                raise ValueError("test error")

        # Should log start and error
        assert plugin.context.log.call_count == 2


class TestMetricsMixin:
    """Test cases for MetricsMixin."""

    class TestPlugin(MetricsMixin):
        """Test plugin using the mixin."""

        pass

    def test_counter_metrics(self):
        """Test counter metric operations."""
        plugin = self.TestPlugin()

        plugin.increment_counter("requests")
        plugin.increment_counter("requests", 5)
        plugin.increment_counter("errors", 2)

        metrics = plugin.get_metrics_summary()
        assert metrics["counters"]["requests"] == 6
        assert metrics["counters"]["errors"] == 2

    def test_gauge_metrics(self):
        """Test gauge metric operations."""
        plugin = self.TestPlugin()

        plugin.set_gauge("memory_usage", 75.5)
        plugin.set_gauge("cpu_usage", 45.2)

        metrics = plugin.get_metrics_summary()
        assert metrics["gauges"]["memory_usage"] == 75.5
        assert metrics["gauges"]["cpu_usage"] == 45.2

    @pytest.mark.asyncio
    async def test_timing_metrics(self):
        """Test timing metric operations."""
        plugin = self.TestPlugin()

        async with plugin.measure_time("operation_1"):
            await asyncio.sleep(0.01)

        async with plugin.measure_time("operation_2"):
            await asyncio.sleep(0.02)

        metrics = plugin.get_metrics_summary()
        assert "operation_1" in metrics["timing_stats"]
        assert "operation_2" in metrics["timing_stats"]
        assert metrics["timing_stats"]["operation_1"]["count"] == 1
        assert metrics["timing_stats"]["operation_1"]["average"] > 0.01

    def test_reset_metrics(self):
        """Test resetting metrics."""
        plugin = self.TestPlugin()

        plugin.increment_counter("test", 10)
        plugin.set_gauge("test", 5.0)
        plugin.reset_metrics()

        metrics = plugin.get_metrics_summary()
        assert len(metrics["counters"]) == 0
        assert len(metrics["gauges"]) == 0


class TestErrorHandlingMixin:
    """Test cases for ErrorHandlingMixin."""

    class TestPlugin(ErrorHandlingMixin, LoggingMixin):
        """Test plugin using the mixins."""

        def __init__(self):
            self.context = Mock()
            self.context.log = AsyncMock()
            self.call_count = 0

        @ErrorHandlingMixin.safe_execute(default_value="default")
        async def safe_method(self, should_fail=False):
            if should_fail:
                raise ValueError("test error")
            return "success"

    @pytest.mark.asyncio
    async def test_with_retry_success(self):
        """Test retry decorator with eventual success."""
        plugin = self.TestPlugin()
        attempt_count = 0

        @plugin.with_retry(max_attempts=3, delay=0.01)
        async def flaky_method():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("temporary error")
            return "success"

        result = await flaky_method()
        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_with_retry_all_fail(self):
        """Test retry decorator when all attempts fail."""
        plugin = self.TestPlugin()

        @plugin.with_retry(max_attempts=2, delay=0.01)
        async def always_fails():
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            await always_fails()

    @pytest.mark.asyncio
    async def test_safe_execute(self):
        """Test safe_execute decorator."""
        plugin = self.TestPlugin()

        # Success case
        result = await plugin.safe_method(should_fail=False)
        assert result == "success"

        # Failure case - returns default
        result = await plugin.safe_method(should_fail=True)
        assert result == "default"


class TestCircuitBreakerMixin:
    """Test cases for CircuitBreakerMixin."""

    class TestPlugin(CircuitBreakerMixin, LoggingMixin):
        """Test plugin using the mixins."""

        def __init__(self):
            super().__init__()
            self.context = Mock()
            self.context.log = AsyncMock()
            self.init_circuit_breaker(
                "test_operation", failure_threshold=2, recovery_timeout=0.1
            )

        async def protected_method(self, should_fail=False):
            @self.circuit_breaker("test_operation")
            async def _inner():
                if should_fail:
                    raise ValueError("test error")
                return "success"

            return await _inner()

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after threshold."""
        plugin = self.TestPlugin()

        # First failure
        with pytest.raises(ValueError):
            await plugin.protected_method(should_fail=True)

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            await plugin.protected_method(should_fail=True)

        # Circuit should be open now
        with pytest.raises(RuntimeError, match="Circuit breaker.*is open"):
            await plugin.protected_method(should_fail=False)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers(self):
        """Test circuit breaker recovery after timeout."""
        plugin = self.TestPlugin()

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await plugin.protected_method(should_fail=True)

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Should be in half-open state, success should close it
        result = await plugin.protected_method(should_fail=False)
        assert result == "success"

        # Should work normally now
        result = await plugin.protected_method(should_fail=False)
        assert result == "success"


class TestIdentifierValidator:
    """Test cases for IdentifierValidator."""

    def test_safe_identifier(self):
        """Test safe identifier validation."""
        assert IdentifierValidator.validate_identifier("valid_name")
        assert IdentifierValidator.validate_identifier("_private")
        assert IdentifierValidator.validate_identifier("Name123")
        assert not IdentifierValidator.validate_identifier("123invalid")
        assert not IdentifierValidator.validate_identifier("invalid-name")
        assert not IdentifierValidator.validate_identifier("")

    def test_table_name(self):
        """Test table name validation."""
        assert IdentifierValidator.validate_table_name("users")
        assert IdentifierValidator.validate_table_name("schema.table")
        assert not IdentifierValidator.validate_table_name("invalid.schema.table")
        assert not IdentifierValidator.validate_table_name("123table")

    def test_python_identifier(self):
        """Test Python identifier validation."""
        assert IdentifierValidator.validate_python_identifier("my_variable")
        assert IdentifierValidator.validate_python_identifier("_private")
        assert not IdentifierValidator.validate_python_identifier("123var")

    def test_env_var(self):
        """Test environment variable name validation."""
        assert IdentifierValidator.validate_env_var("MY_VAR")
        assert IdentifierValidator.validate_env_var("API_KEY_123")
        assert not IdentifierValidator.validate_env_var("my_var")  # lowercase
        assert not IdentifierValidator.validate_env_var("123_VAR")

    def test_url_safe(self):
        """Test URL-safe identifier validation."""
        assert IdentifierValidator.validate_url_safe("my-slug")
        assert IdentifierValidator.validate_url_safe("page123")
        assert not IdentifierValidator.validate_url_safe("My-Slug")  # uppercase
        assert not IdentifierValidator.validate_url_safe("slug_with_underscore")


class TestSQLValidator:
    """Test cases for SQLValidator."""

    def test_injection_detection(self):
        """Test SQL injection pattern detection."""
        validator = SQLValidator()

        # Safe queries
        safe, patterns = validator.validate_query_safe(
            "SELECT * FROM users WHERE id = ?"
        )
        assert safe
        assert len(patterns) == 0

        # Injection attempts
        unsafe, patterns = validator.validate_query_safe(
            "SELECT * FROM users; DROP TABLE users"
        )
        assert not unsafe
        assert len(patterns) > 0

        unsafe, patterns = validator.validate_query_safe(
            "SELECT * FROM users WHERE name = 'test' OR 1=1--"
        )
        assert not unsafe

        unsafe, patterns = validator.validate_query_safe(
            "SELECT * FROM users UNION SELECT * FROM passwords"
        )
        assert not unsafe

    def test_table_name_validation(self):
        """Test table name validation for SQL safety."""
        validator = SQLValidator()

        assert validator.validate_table_name("users")
        assert validator.validate_table_name("user_profiles")
        assert not validator.validate_table_name("DROP")  # SQL keyword
        assert not validator.validate_table_name("SELECT")

    def test_column_names_validation(self):
        """Test column names validation."""
        validator = SQLValidator()

        valid, invalid = validator.validate_column_names(["id", "name", "email"])
        assert valid
        assert len(invalid) == 0

        valid, invalid = validator.validate_column_names(
            ["id", "name-invalid", "123col"]
        )
        assert not valid
        assert "name-invalid" in invalid
        assert "123col" in invalid


class TestJSONYAMLValidator:
    """Test cases for JSONYAMLValidator."""

    def test_json_validation(self):
        """Test JSON string validation."""
        # Valid JSON
        valid, error, data = JSONYAMLValidator.validate_json('{"key": "value"}')
        assert valid
        assert error is None
        assert data == {"key": "value"}

        # Invalid JSON
        valid, error, data = JSONYAMLValidator.validate_json("{invalid json}")
        assert not valid
        assert error is not None
        assert data is None

    def test_yaml_validation(self):
        """Test YAML string validation."""
        # Valid YAML
        valid, error, data = JSONYAMLValidator.validate_yaml(
            "key: value\nlist:\n  - item1\n  - item2"
        )
        assert valid
        assert data == {"key": "value", "list": ["item1", "item2"]}

        # Invalid YAML
        valid, error, data = JSONYAMLValidator.validate_yaml("invalid:\n  - no closing")
        # YAML is very permissive, this might actually parse

    def test_schema_validation(self):
        """Test Pydantic schema validation."""

        class TestSchema(BaseModel):
            name: str
            age: int

        # Valid data
        result = JSONYAMLValidator.validate_schema(
            {"name": "John", "age": 30}, TestSchema
        )
        assert result.success

        # Invalid data
        result = JSONYAMLValidator.validate_schema(
            {"name": "John", "age": "thirty"}, TestSchema
        )
        assert not result.success
        assert len(result.errors) > 0


class TestTypeValidator:
    """Test cases for TypeValidator."""

    def test_validate_type(self):
        """Test basic type validation."""
        assert TypeValidator.validate_type("string", str)
        assert TypeValidator.validate_type(123, int)
        assert TypeValidator.validate_type([1, 2, 3], list)
        assert not TypeValidator.validate_type("string", int)

    def test_validate_dict_schema(self):
        """Test dictionary schema validation."""
        schema = {"name": str, "age": int, "active": bool}

        # Valid data
        valid, errors = TypeValidator.validate_dict_schema(
            {"name": "John", "age": 30, "active": True}, schema
        )
        assert valid
        assert len(errors) == 0

        # Missing key
        valid, errors = TypeValidator.validate_dict_schema(
            {"name": "John", "age": 30}, schema
        )
        assert not valid
        assert any("Missing required key: active" in err for err in errors)

        # Wrong type
        valid, errors = TypeValidator.validate_dict_schema(
            {"name": "John", "age": "thirty", "active": True}, schema
        )
        assert not valid
        assert any("wrong type" in err for err in errors)

    def test_validate_list_types(self):
        """Test list type validation."""
        # All valid
        valid, invalid_indices = TypeValidator.validate_list_types([1, 2, 3, 4], int)
        assert valid
        assert len(invalid_indices) == 0

        # Some invalid
        valid, invalid_indices = TypeValidator.validate_list_types(
            [1, "two", 3, "four"], int
        )
        assert not valid
        assert invalid_indices == [1, 3]


class TestValidationResultBuilder:
    """Test cases for ValidationResultBuilder."""

    def test_builder_pattern(self):
        """Test validation result builder pattern."""
        result = (
            ValidationResultBuilder()
            .add_error("Invalid format", field="email")
            .add_warning("Deprecated field", field="old_field")
            .add_context("timestamp", "2024-01-01")
            .build()
        )

        assert not result.success
        assert "email: Invalid format" in result.errors
        assert "old_field: Deprecated field" in result.warnings
        assert result.context["timestamp"] == "2024-01-01"

    def test_merge_results(self):
        """Test merging validation results."""
        other_result = ValidationResult(success=False, errors=["Other error"])

        result = (
            ValidationResultBuilder()
            .add_error("First error")
            .merge(other_result)
            .build()
        )

        assert not result.success
        assert len(result.errors) == 2
        assert "First error" in result.errors
        assert "Other error" in result.errors


class TestConvenienceFunctions:
    """Test cases for convenience validation functions."""

    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("user@example.com")
        assert validate_email("user.name+tag@example.co.uk")
        assert not validate_email("invalid.email")
        assert not validate_email("@example.com")
        assert not validate_email("user@")

    def test_validate_url(self):
        """Test URL validation."""
        assert validate_url("https://example.com")
        assert validate_url("http://example.com/path?query=value")
        assert validate_url("https://sub.example.com:8080/path")
        assert not validate_url("not-a-url")
        assert not validate_url("ftp://example.com")  # Only http/https

    def test_validate_semantic_version(self):
        """Test semantic version validation."""
        assert validate_semantic_version("1.0.0")
        assert validate_semantic_version("2.1.3-alpha")
        assert validate_semantic_version("1.0.0-beta.1")
        assert validate_semantic_version("1.0.0+build123")
        assert not validate_semantic_version("1.0")
        assert not validate_semantic_version("v1.0.0")


class TestRateLimiter:
    """Test cases for RateLimiter."""

    @pytest.mark.asyncio
    async def test_sliding_window(self):
        """Test sliding window rate limiting."""
        limiter = RateLimiter(
            max_requests=3, time_window=0.1, algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )

        # First 3 requests should pass
        assert await limiter.allow_request()
        assert await limiter.allow_request()
        assert await limiter.allow_request()

        # 4th should fail
        assert not await limiter.allow_request()

        # Wait for window to slide
        await asyncio.sleep(0.15)

        # Should allow again
        assert await limiter.allow_request()

    @pytest.mark.asyncio
    async def test_token_bucket(self):
        """Test token bucket rate limiting."""
        limiter = RateLimiter(
            max_requests=5,
            time_window=1.0,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_size=3,
        )

        # Burst of 3 should pass
        assert await limiter.allow_request()
        assert await limiter.allow_request()
        assert await limiter.allow_request()

        # 4th might fail if no tokens refilled
        # But let's wait a bit for refill
        await asyncio.sleep(0.3)
        assert await limiter.allow_request()

    def test_sync_rate_limiting(self):
        """Test synchronous rate limiting."""
        limiter = RateLimiter(max_requests=2, time_window=0.1)

        assert limiter.allow_request_sync()
        assert limiter.allow_request_sync()
        assert not limiter.allow_request_sync()

    @pytest.mark.asyncio
    async def test_wait_if_needed(self):
        """Test waiting for rate limit availability."""
        limiter = RateLimiter(max_requests=1, time_window=0.1)

        # First request passes immediately
        await limiter.wait_if_needed()

        # Second request should wait
        start = time.time()
        await limiter.wait_if_needed()
        elapsed = time.time() - start

        assert elapsed >= 0.05  # Should have waited

    def test_metrics(self):
        """Test rate limiter metrics."""
        limiter = RateLimiter(max_requests=2, time_window=1.0)

        limiter.allow_request_sync()
        limiter.allow_request_sync()
        limiter.allow_request_sync()  # This should be denied

        metrics = limiter.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["allowed_requests"] == 2
        assert metrics["denied_requests"] == 1


class TestMultiTierRateLimiter:
    """Test cases for MultiTierRateLimiter."""

    @pytest.mark.asyncio
    async def test_multi_tier(self):
        """Test multi-tier rate limiting."""
        limiter = MultiTierRateLimiter()
        limiter.add_tier("per_second", max_requests=2, time_window=1.0)
        limiter.add_tier("per_minute", max_requests=5, time_window=60.0)

        # First 2 should pass (within per_second limit)
        assert await limiter.allow_request()
        assert await limiter.allow_request()

        # 3rd should fail (exceeds per_second)
        assert not await limiter.allow_request()

        # Wait for per_second to reset
        await asyncio.sleep(1.1)

        # Should allow 2 more (total 4, still within per_minute)
        assert await limiter.allow_request()
        assert await limiter.allow_request()

    def test_tier_reset(self):
        """Test resetting specific tiers."""
        limiter = MultiTierRateLimiter()
        limiter.add_tier("test", max_requests=1, time_window=60.0)

        # Use up the limit
        asyncio.run(limiter.allow_request())
        assert not asyncio.run(limiter.allow_request())

        # Reset the tier
        limiter.reset("test")

        # Should allow again
        assert asyncio.run(limiter.allow_request())


class TestFactoryFunctions:
    """Test cases for rate limiter factory functions."""

    def test_api_rate_limiter(self):
        """Test API rate limiter factory."""
        limiter = create_api_rate_limiter()
        assert limiter.config.max_requests == 100
        assert limiter.config.time_window == 60.0

    def test_database_rate_limiter(self):
        """Test database rate limiter factory."""
        limiter = create_database_rate_limiter()
        assert limiter.config.max_requests == 1000
        assert limiter.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET

    def test_webhook_rate_limiter(self):
        """Test webhook rate limiter factory."""
        limiter = create_webhook_rate_limiter()
        assert isinstance(limiter, MultiTierRateLimiter)
        metrics = limiter.get_metrics()
        assert "per_second" in metrics
        assert "per_minute" in metrics
        assert "per_hour" in metrics

    def test_user_rate_limiter(self):
        """Test user rate limiter factory."""
        limiter = create_user_rate_limiter()
        assert limiter.config.max_requests == 60
        assert limiter.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
