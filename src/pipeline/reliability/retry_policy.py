from __future__ import annotations

"""Asynchronous retry helper using ``tenacity``."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from tenacity import (AsyncRetrying, RetryError, stop_after_attempt,
                      wait_exponential)


@dataclass
class RetryPolicy:
    """Execute a coroutine with retries and exponential backoff."""

    attempts: int = 3
    backoff: float = 1.0

    async def execute(
        self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        retry = AsyncRetrying(
            stop=stop_after_attempt(self.attempts),
            wait=wait_exponential(multiplier=self.backoff),
            reraise=True,
        )
        try:
            async for attempt in retry:  # pragma: no cover - control flow
                with attempt:
                    return await func(*args, **kwargs)
        except RetryError as exc:  # pragma: no cover - bubble up original
            raise exc.last_attempt.result()
