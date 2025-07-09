"""Demonstrate CacheResource with an in-memory backend.

Run with ``python -m examples.cache_example`` or install the package in editable
mode.
"""

from __future__ import annotations

import asyncio

from .utilities import enable_plugins_namespace

enable_plugins_namespace()

from user_plugins.resources.cache import CacheResource, InMemoryCache


async def main() -> None:
    cache = CacheResource(InMemoryCache())
    await cache.set("greeting", "hello world")
    print("Cached value:", await cache.get("greeting"))
    await cache.clear()


if __name__ == "__main__":
    asyncio.run(main())
