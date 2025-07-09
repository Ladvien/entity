"""Demonstrate streaming and function-calling with a simple echo LLM.

Run with ``python -m examples.advanced_llm`` or install the package in
editable mode.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from .utilities import enable_plugins_namespace

enable_plugins_namespace()


class EchoLLM:
    """Minimal LLM stub returning the prompt back."""

    async def stream(self, prompt: str):
        for word in prompt.split():
            yield word + " "

    async def generate(
        self, prompt: str, functions: list[Dict[str, Any]] | None = None
    ):
        return type("LLMResponse", (), {"content": prompt, "metadata": {}})()


def create_llm() -> EchoLLM:
    """Return a simple echo LLM instance."""

    return EchoLLM()


async def main() -> None:
    llm = create_llm()

    print("Streaming response:")
    async for chunk in llm.stream("Tell me a joke about penguins"):
        print(chunk, end="", flush=True)
    print("\n")

    functions: list[Dict[str, Any]] = [
        {
            "name": "get_weather",
            "description": "Return the weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
            },
        }
    ]
    resp = await llm.generate("What is the weather in Paris?", functions=functions)
    print("Function call metadata:", resp.metadata.get("function_call"))
    print("Response:", resp.content)


if __name__ == "__main__":
    asyncio.run(main())
