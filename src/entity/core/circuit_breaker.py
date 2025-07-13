from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, TypeVar

from entity.config.models import BreakerSettings, CircuitBreakerConfig
from entity.pipeline.exceptions import CircuitBreakerTripped

T = TypeVar("T")


class RetryPolicy:
    """Retry asynchronous operations with optional backoff."""

    def __init__(self, *, attempts: int = 3, backoff: float = 0.1) -> None:
        self.attempts = attempts
        self.backoff = backoff

    async def execute(
        self, func: Callable[..., Awaitable[T]], *args: object, **kwargs: object
    ) -> T:
        for attempt in range(self.attempts):
            try:
                return await func(*args, **kwargs)
            except Exception:  # noqa: BLE001
                if attempt >= self.attempts - 1:
                    raise
                await asyncio.sleep(self.backoff * (2**attempt))
        raise RuntimeError("unreachable")


class CircuitBreaker:
    """Stop calls when failures exceed a threshold."""

    def __init__(
        self, *, failure_threshold: int = 3, recovery_timeout: float = 60.0
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._tripped_at: float | None = None

    def _reset_if_needed(self) -> None:
        if (
            self._tripped_at is not None
            and time.monotonic() - self._tripped_at >= self.recovery_timeout
        ):
            self.reset()

    async def call(
        self, func: Callable[..., Awaitable[T]], *args: object, **kwargs: object
    ) -> T:
        self._reset_if_needed()
        if self._failure_count >= self.failure_threshold:
            raise CircuitBreakerTripped("circuit breaker open")
        try:
            result = await func(*args, **kwargs)
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._tripped_at = time.monotonic()
            raise
        else:
            self.reset()
            return result

    def reset(self) -> None:
        self._failure_count = 0
        self._tripped_at = None

    @property
    def failure_count(self) -> int:
        """Return the current consecutive failure count."""

        return self._failure_count

    @property
    def is_open(self) -> bool:
        """Return ``True`` if the breaker is tripped."""

        return self._failure_count >= self.failure_threshold


@dataclass
class BreakerManager:
    """Provide breakers for resource categories."""

    default: CircuitBreaker
    category_breakers: Dict[str, CircuitBreaker]

    def get(self, category: str | None) -> CircuitBreaker:
        if not category:
            return self.default
        if category not in self.category_breakers:
            self.category_breakers[category] = CircuitBreaker(
                failure_threshold=self.default.failure_threshold,
                recovery_timeout=self.default.recovery_timeout,
            )
        return self.category_breakers[category]

    @classmethod
    def from_config(
        cls, cfg: CircuitBreakerConfig, settings: BreakerSettings
    ) -> "BreakerManager":
        cat_breakers = {
            "database": CircuitBreaker(
                failure_threshold=cfg.database or settings.database.failure_threshold,
                recovery_timeout=cfg.recovery_timeout,
            ),
            "api": CircuitBreaker(
                failure_threshold=cfg.api or settings.external_api.failure_threshold,
                recovery_timeout=cfg.recovery_timeout,
            ),
            "filesystem": CircuitBreaker(
                failure_threshold=cfg.filesystem
                or settings.file_system.failure_threshold,
                recovery_timeout=cfg.recovery_timeout,
            ),
        }
        default = CircuitBreaker(
            failure_threshold=cfg.failure_threshold,
            recovery_timeout=cfg.recovery_timeout,
        )
        return cls(default, cat_breakers)


__all__ = ["CircuitBreaker", "CircuitBreakerTripped", "RetryPolicy", "BreakerManager"]
