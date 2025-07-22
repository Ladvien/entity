from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List, Optional


# --- Plugins -----------------------------------------------------------------


class Plugin:
    async def run(self, context: Dict[str, Any]) -> None:
        pass


class InputPlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["parsed"] = context["input"]


class ParsePlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["thoughts"] = context["parsed"]


class ThinkPlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["action"] = context["thoughts"]


class DoPlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["result"] = context.get("action", "")


class ReviewPlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["final"] = context.get("result", "")


class OutputPlugin(Plugin):
    async def run(self, context: Dict[str, Any]) -> None:
        context["response"] = context.get("final", "")


# --- Agent -------------------------------------------------------------------


DEFAULT_PLUGINS = {
    "input": [InputPlugin()],
    "parse": [ParsePlugin()],
    "think": [ThinkPlugin()],
    "do": [DoPlugin()],
    "review": [ReviewPlugin()],
    "output": [OutputPlugin()],
}


class Agent:
    def __init__(
        self,
        resources: Optional[Iterable[Any]] = None,
        workflow: Optional[Dict[str, List[Plugin]]] = None,
    ) -> None:
        self.resources = list(resources) if resources else []
        self.workflow = workflow or DEFAULT_PLUGINS

    async def setup(self) -> None:
        await asyncio.gather(*(r.setup() for r in self.resources))

    async def chat(self, message: str) -> str:
        context: Dict[str, Any] = {"input": message}
        for stage in ["input", "parse", "think", "do", "review", "output"]:
            for plugin in self.workflow.get(stage, []):
                await plugin.run(context)
        return context.get("response", "")
