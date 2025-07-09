"""Demonstrate LoggingAdapter and structured logging.

Run with ``python -m examples.structured_logging_example`` or install the
package in editable mode.
"""

from __future__ import annotations

import asyncio


from .utilities import enable_plugins_namespace

enable_plugins_namespace()

import logging


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("structured_logging_example")
    logger.info("Structured logging active")


if __name__ == "__main__":
    asyncio.run(main())
