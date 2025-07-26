from __future__ import annotations

"""Demonstrate a multi-stage agent.

All resources are prepared automatically. Any initialization errors are
reported to the console.
"""

import asyncio

from entity.core.agent import Agent
from entity.defaults import load_defaults
from entity.setup.ollama_installer import OllamaInstaller


async def main() -> None:
    try:
        resources = load_defaults()
    except Exception as exc:  # pragma: no cover - example runtime guard
        print(
            "Failed to initialize resources. "
            "Automatic Ollama installation may have failed.\n"
            "Try installing manually with:\n"
            "  curl -fsSL https://ollama.com/install.sh | sh\n"
            "or set ENTITY_AUTO_INSTALL_OLLAMA=false to skip.\n"
            f"Details: {exc}"
        )
        return

    if not resources["llm"].health_check():
        print(
            "Warning: Ollama service is unreachable. "
            "Ensure it is running on http://localhost:11434 "
            "if results seem incorrect."
        )

    agent = Agent.from_workflow("examples/advanced_workflow.yaml", resources=resources)
    result = await agent.chat("2 + 2")
    print(result["response"])


if __name__ == "__main__":
    asyncio.run(main())
