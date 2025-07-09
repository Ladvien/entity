"""Demonstrate basic Memory usage."""

from __future__ import annotations

import asyncio

from entity.resources.memory import Memory


async def main() -> None:
    memory = Memory()
    memory.remember("greeting", "hello world")
    print("Stored value:", memory.get("greeting"))
    memory.clear()


if __name__ == "__main__":
    asyncio.run(main())
