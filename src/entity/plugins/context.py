from __future__ import annotations

from typing import Any, Dict, List

from entity.tools.sandbox import SandboxedToolRunner
from entity.tools.registry import ToolInfo
from pydantic import BaseModel, ValidationError


class WorkflowContext:
    """Simple context passed to plugins during execution."""

    def __init__(self) -> None:
        self._response: str | None = None
        self.current_stage: str | None = None
        self.message: str | None = None

    def say(self, message: str) -> None:
        """Store the final response only during the OUTPUT stage."""

        from entity.workflow.executor import WorkflowExecutor

        if self.current_stage != WorkflowExecutor.OUTPUT:
            raise RuntimeError("context.say() only allowed in OUTPUT stage")

        self._response = message

    @property
    def response(self) -> str | None:  # noqa: D401
        """Return the response set by :py:meth:`say`."""
        return self._response


class PluginContext(WorkflowContext):
    """Extended context exposing memory and resources."""

    def __init__(
        self,
        resources: Dict[str, Any],
        user_id: str,
        memory: Any | None = None,
    ) -> None:
        # TODO: Refactor for readability
        super().__init__()
        self._resources = resources
        self.user_id = user_id
        self._memory = memory if memory is not None else resources.get("memory")
        if self._memory is None:
            raise RuntimeError("Memory resource required")
        self._conversation: List[str] = []
        tools_src = resources.get("tools", {})
        self._tools: Dict[str, ToolInfo] = {}
        for t_name, t in tools_src.items():
            if isinstance(t, ToolInfo):
                self._tools[t_name] = t
            else:
                self._tools[t_name] = ToolInfo(t_name, t)
        self._tool_queue: List[tuple[str, Dict[str, Any]]] = []
        self.logger = resources.get("logging")
        self.metrics_collector = resources.get("metrics_collector")
        self.sandbox = resources.get("sandbox", SandboxedToolRunner())

    async def remember(self, key: str, value: Any) -> None:
        """Persist value namespaced by ``user_id``."""
        namespaced = f"{self.user_id}:{key}"
        await self._memory.store(namespaced, value)

    async def recall(self, key: str, default: Any | None = None) -> Any:
        """Retrieve stored value for ``key`` or ``default``."""
        namespaced = f"{self.user_id}:{key}"
        return await self._memory.load(namespaced, default)

    def say(self, message: str) -> None:  # type: ignore[override]
        super().say(message)
        self._conversation.append(message)

    async def load_state(self) -> None:
        """Load persistent conversation state."""
        self._conversation = await self.recall("conversation", [])

    async def flush_state(self) -> None:
        """Persist conversation state."""
        await self.remember("conversation", self._conversation)

    def listen(self) -> str | None:
        """Return the last user message."""
        return self.message

    def conversation(self) -> List[str]:
        """Return conversation history including outputs."""

        history = list(self._conversation)
        if self.message:
            history.insert(0, self.message)
        return history

    def get_resource(self, name: str) -> Any:
        """Return a resource by name."""
        return self._resources.get(name)

    async def tool_use(self, name: str, **kwargs: Any) -> Any:
        """Execute a registered tool immediately using the sandbox."""
        tool: ToolInfo | None = self._tools.get(name)
        if tool is None:
            raise RuntimeError(f"Tool '{name}' not found")

        if tool.input_model is not None:
            try:
                validated = tool.input_model(**kwargs)
            except ValidationError as exc:
                raise RuntimeError(f"Invalid input for tool {name}: {exc}") from exc
            kwargs = validated.model_dump()

        result = await self.sandbox.run(tool.func, **kwargs)

        if tool.output_model is not None:
            if isinstance(result, tool.output_model):
                return result
            return tool.output_model.model_validate(result)
        return result

    def queue_tool_use(self, name: str, **kwargs: Any) -> None:
        """Add a tool call to be executed later."""
        self._tool_queue.append((name, kwargs))

    async def run_tool_queue(self) -> None:
        """Execute all queued tools in order."""
        while self._tool_queue:
            name, kwargs = self._tool_queue.pop(0)
            await self.tool_use(name, **kwargs)

    def discover_tools(self, **filters: Any):
        """Return registered tools filtered by ``filters``."""
        from entity.tools.registry import discover_tools

        return discover_tools(**filters)
