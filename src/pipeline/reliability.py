from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, TypeVar

from .exceptions import CircuitBreakerTripped

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


__all__ = ["RetryPolicy", "CircuitBreaker"]
