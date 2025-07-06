from __future__ import annotations

"""OpenTelemetry tracing helpers for the Entity pipeline."""

import os
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

from opentelemetry import trace

try:  # Optional dependency
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
        OTLPSpanExporter
except Exception:  # pragma: no cover - optional
    OTLPSpanExporter = None  # type: ignore
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)


def _get_exporter():
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint and OTLPSpanExporter is not None:
        return OTLPSpanExporter(endpoint=endpoint)
    return ConsoleSpanExporter()


_tracer_provider = TracerProvider(resource=Resource.create({"service.name": "entity"}))
_tracer_provider.add_span_processor(BatchSpanProcessor(_get_exporter()))
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
