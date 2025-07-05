from __future__ import annotations

"""Simple helpers for measuring memory usage."""

from typing import Any, Awaitable, Callable, Tuple

import psutil


async def profile_memory(
    func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
) -> Tuple[Any, int]:
    """Run ``func`` and return its result along with memory difference in bytes."""
    process = psutil.Process()
    before = process.memory_info().rss
    result = await func(*args, **kwargs)
    after = process.memory_info().rss
    return result, after - before


__all__ = ["profile_memory"]
