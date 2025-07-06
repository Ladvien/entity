"""Demonstrate streaming and function-calling with UnifiedLLMResource."""

"""Demonstrate streaming and function-calling with UnifiedLLMResource."""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys
from typing import Any, Dict

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.contrib.llm.unified import UnifiedLLMResource


def create_llm() -> UnifiedLLMResource:
    """Return a configured LLM resource.

    Falls back to :class:`EchoProvider` when ``OLLAMA_BASE_URL`` or ``OLLAMA_MODEL``
    is not defined.
    """

    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    if base_url and model:
        cfg = {"provider": "ollama", "base_url": base_url, "model": model}
    else:
        cfg = {"provider": "echo"}
    return UnifiedLLMResource(cfg)


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
