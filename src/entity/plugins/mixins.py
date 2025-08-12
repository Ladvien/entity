"""Reusable mixins for plugins to reduce code duplication."""

from __future__ import annotations

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ValidationError

from entity.plugins.validation import ValidationResult
from entity.resources.logging import LogCategory, LogLevel


class ConfigValidationMixin:
    """Mixin for consistent configuration validation across plugins."""

    class ConfigModel(BaseModel):
        """Default empty configuration model to be overridden."""

        class Config:
            extra = "forbid"

    def validate_config_strict(self) -> None:
        """Validate configuration and raise on any errors."""
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(
                f"{self.__class__.__name__} configuration validation failed: "
                f"{', '.join(validation_result.errors)}"
            )

    def validate_config_with_defaults(self, defaults: Dict[str, Any]) -> None:
        """Validate configuration with default values applied."""
        if not hasattr(self, "config") or self.config is None:
            self.config = {}

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        self.validate_config_strict()

    def validate_config_custom(self, error_prefix: str = "") -> ValidationResult:
        """Validate with custom error message prefix."""
        try:
            self.config = self.ConfigModel(**self.config)
            return ValidationResult.success()
        except ValidationError as exc:
            errors = [f"{error_prefix}{err}" for err in str(exc).split("\n")]
            return ValidationResult(success=False, errors=errors)


class LoggingMixin:
    """Mixin for standardized logging across plugins."""

    async def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message with plugin context."""
        if hasattr(self, "context"):
            await self.context.log(
                LogLevel.DEBUG,
                LogCategory.PLUGIN_LIFECYCLE,
                f"[{self.__class__.__name__}] {message}",
                **kwargs,
            )

    async def log_info(self, message: str, **kwargs) -> None:
        """Log info message with plugin context."""
        if hasattr(self, "context"):
            await self.context.log(
                LogLevel.INFO,
                LogCategory.PLUGIN_LIFECYCLE,
                f"[{self.__class__.__name__}] {message}",
                **kwargs,
            )

    async def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message with plugin context."""
        if hasattr(self, "context"):
            await self.context.log(
                LogLevel.WARNING,
                LogCategory.PLUGIN_LIFECYCLE,
                f"[{self.__class__.__name__}] {message}",
                **kwargs,
            )

    async def log_error(
        self, message: str, exception: Optional[Exception] = None, **kwargs
    ) -> None:
        """Log error message with plugin context."""
        if hasattr(self, "context"):
            error_details = kwargs.copy()
            if exception:
                error_details["exception"] = str(exception)
                error_details["exception_type"] = exception.__class__.__name__

            await self.context.log(
                LogLevel.ERROR,
                LogCategory.PLUGIN_LIFECYCLE,
                f"[{self.__class__.__name__}] {message}",
                **error_details,
            )

    @asynccontextmanager
    async def log_operation(self, operation_name: str):
        """Context manager for logging operation start/end with timing."""
        start_time = time.time()
        await self.log_debug(f"Starting {operation_name}")
        try:
            yield
            elapsed = time.time() - start_time
            await self.log_debug(f"Completed {operation_name} in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            await self.log_error(
                f"Failed {operation_name} after {elapsed:.2f}s", exception=e
            )
            raise


class MetricsMixin:
    """Mixin for metrics collection in plugins."""

    def __init__(self, *args, **kwargs):
        """Initialize metrics storage."""
        super().__init__(*args, **kwargs)
        self._metrics: Dict[str, Any] = {
            "counters": {},
            "gauges": {},
            "timings": [],
        }

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        if name not in self._metrics["counters"]:
            self._metrics["counters"][name] = 0
        self._metrics["counters"][name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value."""
        self._metrics["gauges"][name] = value

    def record_timing(self, name: str, duration: float) -> None:
        """Record a timing measurement."""
        self._metrics["timings"].append(
            {"name": name, "duration": duration, "timestamp": time.time()}
        )

    @asynccontextmanager
    async def measure_time(self, metric_name: str):
        """Context manager to measure and record execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timing(metric_name, duration)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        timing_stats = {}
        if self._metrics["timings"]:
            grouped_timings = {}
            for timing in self._metrics["timings"]:
                name = timing["name"]
                if name not in grouped_timings:
                    grouped_timings[name] = []
                grouped_timings[name].append(timing["duration"])

            for name, durations in grouped_timings.items():
                timing_stats[name] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }

        return {
            "counters": self._metrics["counters"].copy(),
            "gauges": self._metrics["gauges"].copy(),
            "timing_stats": timing_stats,
        }

    def reset_metrics(self) -> None:
        """Reset all metrics to initial state."""
        self._metrics = {
            "counters": {},
            "gauges": {},
            "timings": [],
        }


class ErrorHandlingMixin:
    """Mixin for standardized error handling in plugins."""

    def with_retry(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
    ):
        """Decorator for automatic retry logic."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                attempt_delay = delay

                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            if hasattr(self, "log_warning"):
                                await self.log_warning(
                                    f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                                )
                            await asyncio.sleep(attempt_delay)
                            attempt_delay *= backoff
                        else:
                            if hasattr(self, "log_error"):
                                await self.log_error(
                                    f"All {max_attempts} attempts failed for {func.__name__}",
                                    exception=e,
                                )

                raise last_exception

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                attempt_delay = delay

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            time.sleep(attempt_delay)
                            attempt_delay *= backoff

                raise last_exception

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    @staticmethod
    def safe_execute(default_value: Any = None, log_errors: bool = True):
        """Decorator to safely execute functions with default return on error."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    if log_errors and hasattr(self, "log_error"):
                        await self.log_error(f"Error in {func.__name__}", exception=e)
                    return default_value

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                try:
                    return func(self, *args, **kwargs)
                except Exception:
                    return default_value

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator


class CircuitBreakerMixin:
    """Mixin for circuit breaker pattern implementation."""

    def __init__(self, *args, **kwargs):
        """Initialize circuit breaker state."""
        super().__init__(*args, **kwargs)
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}

    def init_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ) -> None:
        """Initialize a circuit breaker for a specific operation."""
        self._circuit_breakers[name] = {
            "state": "closed",
            "failure_count": 0,
            "failure_threshold": failure_threshold,
            "recovery_timeout": recovery_timeout,
            "last_failure_time": None,
            "expected_exception": expected_exception,
        }

    def circuit_breaker(self, name: str):
        """Decorator to apply circuit breaker pattern to a method."""
        if name not in self._circuit_breakers:
            self.init_circuit_breaker(name)

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                breaker = self._circuit_breakers[name]

                if breaker["state"] == "open":
                    if (
                        breaker["last_failure_time"]
                        and time.time() - breaker["last_failure_time"]
                        > breaker["recovery_timeout"]
                    ):
                        breaker["state"] = "half_open"
                        breaker["failure_count"] = 0
                    else:
                        raise RuntimeError(f"Circuit breaker '{name}' is open")

                try:
                    result = await func(*args, **kwargs)
                    if breaker["state"] == "half_open":
                        breaker["state"] = "closed"
                    breaker["failure_count"] = 0
                    return result

                except breaker["expected_exception"] as e:
                    breaker["failure_count"] += 1
                    breaker["last_failure_time"] = time.time()

                    if breaker["failure_count"] >= breaker["failure_threshold"]:
                        breaker["state"] = "open"
                        if hasattr(self, "log_error"):
                            await self.log_error(
                                f"Circuit breaker '{name}' opened after {breaker['failure_count']} failures"
                            )

                    raise e

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                breaker = self._circuit_breakers[name]

                if breaker["state"] == "open":
                    if (
                        breaker["last_failure_time"]
                        and time.time() - breaker["last_failure_time"]
                        > breaker["recovery_timeout"]
                    ):
                        breaker["state"] = "half_open"
                        breaker["failure_count"] = 0
                    else:
                        raise RuntimeError(f"Circuit breaker '{name}' is open")

                try:
                    result = func(*args, **kwargs)
                    if breaker["state"] == "half_open":
                        breaker["state"] = "closed"
                    breaker["failure_count"] = 0
                    return result

                except breaker["expected_exception"] as e:
                    breaker["failure_count"] += 1
                    breaker["last_failure_time"] = time.time()

                    if breaker["failure_count"] >= breaker["failure_threshold"]:
                        breaker["state"] = "open"

                    raise e

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_circuit_breaker_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a circuit breaker."""
        if name in self._circuit_breakers:
            breaker = self._circuit_breakers[name].copy()
            breaker.pop("expected_exception")
            return breaker
        return None
