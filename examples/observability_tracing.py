"""Demonstrate basic tracing with OpenTelemetry.

Run with ``python -m examples.observability_tracing`` or install the package in
editable mode.
"""

from __future__ import annotations

import asyncio

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline.observability import start_span


async def main() -> None:
    async with start_span("observability_tracing"):
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
