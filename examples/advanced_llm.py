"""Demonstrate streaming and function-calling with UnifiedLLMResource."""

import asyncio
import pathlib
import sys
from typing import Any, Dict

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))


def _enable_plugins_namespace() -> None:
    import importlib
    import pkgutil
    import types

    import pipeline.plugins
    import pipeline.plugins.resources as plugin_resources
    import pipeline.resources

    plugins_mod = types.ModuleType("plugins")
    plugins_mod.__dict__.update(vars(pipeline.plugins))
    sys.modules["plugins"] = plugins_mod
    sys.modules["plugins.resources"] = plugin_resources
    plugins_mod.resources = plugin_resources

    for _, name, _ in pkgutil.walk_packages(
        pipeline.resources.__path__, prefix="pipeline.resources."
    ):
        module = importlib.import_module(name)
        alias = name.replace("pipeline.resources.", "plugins.")
        sys.modules[alias] = module
        parent_alias = alias.rsplit(".", 1)[0]
        if parent_alias == "plugins":
            setattr(plugins_mod, alias.split(".")[-1], module)
        else:
            parent = sys.modules.setdefault(
                parent_alias, types.ModuleType(parent_alias)
            )
            setattr(parent, alias.split(".")[-1], module)


_enable_plugins_namespace()

from plugins.llm.unified import UnifiedLLMResource


async def main() -> None:
    llm = UnifiedLLMResource(
        {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "tinyllama",
        }
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
