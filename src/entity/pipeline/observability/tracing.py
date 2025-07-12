from __future__ import annotations

"""Minimal tracing utilities used throughout the pipeline."""

from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

# Telemetry integration is currently disabled. These helpers provide the same
# interface without relying on OpenTelemetry.


class _Span:  # pragma: no cover - simple placeholder
    """No-op span object used when tracing is disabled."""

    def __enter__(self) -> "_Span":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


@asynccontextmanager
async def start_span(name: str):  # pragma: no cover - trivial
    """Yield a no-op span to maintain tracing API compatibility."""
    span = _Span()
    try:
        yield span
    finally:
        pass


async def traced(
    name: str, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
) -> Any:
    """Run ``func`` inside a span named ``name``."""
    async with start_span(name):
        return await func(*args, **kwargs)
