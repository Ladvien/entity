from __future__ import annotations

from typing import List, Dict, Optional, Any, Iterable
import asyncio


class Resource:
    async def setup(self) -> None:
        pass


class Memory(Resource):
    def __init__(self, path: str = "./agent_memory.duckdb") -> None:
        self.path = path

    async def setup(self) -> None:
        # placeholder for creating a DuckDB database
        pass


class LLM(Resource):
    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"
    ) -> None:
        self.base_url = base_url
        self.model = model

    async def setup(self) -> None:
        # placeholder for ensuring Ollama model is ready
        pass


class Storage(Resource):
    def __init__(self, base_path: str = "./agent_files") -> None:
        self.base_path = base_path

    async def setup(self) -> None:
        pass


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
        resources: Optional[Iterable[Resource]] = None,
        workflow: Optional[Dict[str, List[Plugin]]] = None,
    ) -> None:
        self.resources = list(resources) if resources else [Memory(), LLM(), Storage()]
        self.workflow = workflow or DEFAULT_PLUGINS

    async def setup(self) -> None:
        await asyncio.gather(*(r.setup() for r in self.resources))

    async def chat(self, message: str) -> str:
        context: Dict[str, Any] = {"input": message}
        for stage in ["input", "parse", "think", "do", "review", "output"]:
            for plugin in self.workflow.get(stage, []):
                await plugin.run(context)
        return context.get("response", "")
