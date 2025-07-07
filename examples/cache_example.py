"""Demonstrate CacheResource with an in-memory backend."""

from __future__ import annotations

import asyncio
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from user_plugins.resources.cache import CacheResource
from pipeline.cache import InMemoryCache


async def main() -> None:
    cache = CacheResource(InMemoryCache())
    await cache.set("greeting", "hello world")
    print("Cached value:", await cache.get("greeting"))
    await cache.clear()


if __name__ == "__main__":
    asyncio.run(main())
