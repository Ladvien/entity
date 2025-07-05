from __future__ import annotations

"""Simple exponential backoff utilities."""

import asyncio


def compute_delay(
    attempt: int, base: float = 1.0, factor: float = 2.0, max_delay: float | None = None
) -> float:
    """Return the backoff delay for ``attempt`` starting at ``base`` seconds."""
    delay = base * (factor ** max(attempt - 1, 0))
    if max_delay is not None:
        delay = min(delay, max_delay)
    return delay


async def sleep(
    attempt: int, base: float = 1.0, factor: float = 2.0, max_delay: float | None = None
) -> None:
    """Sleep for the computed delay based on ``attempt``."""
    await asyncio.sleep(compute_delay(attempt, base, factor, max_delay))


__all__ = ["compute_delay", "sleep"]
