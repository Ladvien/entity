"""Demonstrate streaming and function-calling with UnifiedLLMResource."""

import asyncio
import pathlib
import sys
from typing import Any, Dict

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

<<<<<<< HEAD
from config.environment import load_env
from pipeline.config import ConfigLoader
=======
>>>>>>> ade5ea02fe57934389c67708aacbf514ac2c4c3b
from pipeline.resources.llm.unified import UnifiedLLMResource


async def main() -> None:
<<<<<<< HEAD
    load_env()
    llm = UnifiedLLMResource(
        ConfigLoader.from_dict(
            {
                "provider": "ollama",
                "base_url": "${OLLAMA_BASE_URL}",
                "model": "${OLLAMA_MODEL}",
            }
        )
=======
    llm = UnifiedLLMResource(
        {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "tinyllama",
        }
>>>>>>> ade5ea02fe57934389c67708aacbf514ac2c4c3b
    )

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
