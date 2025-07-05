"""Configure StructuredLogging and write a single log entry."""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.resources.structured_logging import StructuredLogging

from pipeline.logging import get_logger


async def main() -> None:
    logging_cfg = {"level": "INFO", "json": True}
    plugin = StructuredLogging(logging_cfg)
    await plugin.initialize()

    logger = get_logger("structured_logging_example")
    logger.info("Logging configured successfully")


if __name__ == "__main__":
    asyncio.run(main())
