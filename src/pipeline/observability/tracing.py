from __future__ import annotations

"""OpenTelemetry tracing helpers for the Entity pipeline."""

from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

_tracer_provider = TracerProvider(resource=Resource.create({"service.name": "entity"}))
_tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(_tracer_provider)
_tracer = trace.get_tracer(__name__)


@asynccontextmanager
async def start_span(name: str):
    with _tracer.start_as_current_span(name) as span:
        yield span


async def traced(
    name: str, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
) -> Any:
    """Run ``func`` inside a span named ``name``."""
    async with start_span(name):
        return await func(*args, **kwargs)
