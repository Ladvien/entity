"""Demonstrate basic plugin workflow."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from ..utilities import enable_plugins_namespace

enable_plugins_namespace()


class EchoLLM:
    async def generate(self, prompt: str, **_: Any) -> str:
        return prompt


def create_llm() -> EchoLLM:
    return EchoLLM()


async def main() -> None:
    llm = create_llm()
    print(await llm.generate("hello"))


if __name__ == "__main__":
    asyncio.run(main())
