from __future__ import annotations

"""Simple circuit breaker using :mod:`tenacity` for timing."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from tenacity import RetryError

from ..exceptions import CircuitBreakerTripped
from .retry_policy import RetryPolicy


@dataclass
class CircuitBreaker:
    """Prevent calls when failures exceed a threshold."""

    failure_threshold: int = 3
    recovery_timeout: float = 60.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    _failure_count: int = field(default=0, init=False)
    _last_failure: float = field(default=0.0, init=False)

    def _circuit_open(self) -> bool:
        if self._failure_count < self.failure_threshold:
            return False
        if time.time() - self._last_failure > self.recovery_timeout:
            self._failure_count = 0
            return False
        return True

    async def call(
        self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute ``func`` unless the circuit is open."""
        if self._circuit_open():
            raise CircuitBreakerTripped(func.__name__)
        try:
            result = await self.retry_policy.execute(func, *args, **kwargs)
            self._failure_count = 0
            return result
        except RetryError as exc:
            self._failure_count += 1
            self._last_failure = time.time()
            raise exc.last_attempt.result()
        except Exception:
            self._failure_count += 1
            self._last_failure = time.time()
            raise
