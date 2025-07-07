"""Demonstrate basic tracing with OpenTelemetry."""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline.observability import start_span


async def main() -> None:
    async with start_span("observability_tracing"):
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
