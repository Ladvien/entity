"""Demonstrate LoggingAdapter and structured logging."""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.adapters.logging import LoggingAdapter
from plugins.builtin.adapters.logging_adapter import configure_logging, get_logger


async def main() -> None:
    configure_logging(level="INFO", json_enabled=True)
    adapter = LoggingAdapter()

    logger = get_logger("structured_logging_example")
    logger.info("Logging configured successfully")

    class FakeState:
        def __init__(self) -> None:
            self.response = {"message": "hello"}

    class FakeContext:
        def __init__(self) -> None:
            self.state = FakeState()

        @property
        def response(self):
            return self.state.response

    await adapter.execute(FakeContext())


if __name__ == "__main__":
    asyncio.run(main())
