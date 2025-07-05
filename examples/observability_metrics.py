"""Start Prometheus metrics and trace a simple asynchronous task."""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from pipeline.observability import start_metrics_server, start_span


async def sample_task() -> None:
    async with start_span("sample_task"):
        await asyncio.sleep(0.2)


async def main() -> None:
    start_metrics_server(port=9001)
    await sample_task()


if __name__ == "__main__":
    asyncio.run(main())
