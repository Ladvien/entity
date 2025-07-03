from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from registry import SystemRegistries

from .builder import AgentBuilder
from .runtime import AgentRuntime


@dataclass
class Agent:
    """High level agent wrapper combining builder and runtime."""

    config_path: str | None = None
    builder: AgentBuilder = field(default_factory=AgentBuilder)
    _runtime: AgentRuntime | None = None

    # ------------------------------------------------------------------
    # Delegated plugin helpers
    # ------------------------------------------------------------------
    def add_plugin(self, plugin: Any) -> None:  # pragma: no cover - delegation
        self.builder.add_plugin(plugin)

    def plugin(
        self, func: Optional[Callable] = None, **hints
    ):  # pragma: no cover - delegation
        return self.builder.plugin(func, **hints)

    def load_plugins_from_directory(
        self, directory: str
    ) -> None:  # pragma: no cover - delegation
        self.builder.load_plugins_from_directory(directory)

    def load_plugins_from_package(
        self, package_name: str
    ) -> None:  # pragma: no cover - delegation
        self.builder.load_plugins_from_package(package_name)

    @classmethod
    def from_directory(cls, directory: str) -> "Agent":
        agent = cls()
        agent.load_plugins_from_directory(directory)
        return agent

    @classmethod
    def from_package(cls, package_name: str) -> "Agent":
        agent = cls()
        agent.load_plugins_from_package(package_name)
        return agent

    # ------------------------------------------------------------------
    async def _ensure_runtime(self) -> None:
        if self._runtime is None:
            if self.config_path:
                from .initializer import SystemInitializer

                initializer = SystemInitializer.from_yaml(self.config_path)
                registries = await initializer.initialize()
                self._runtime = AgentRuntime(registries)
            else:
                self._runtime = self.builder.build_runtime()

    @property
    def runtime(self) -> AgentRuntime:
        if self._runtime is None:
            raise RuntimeError("Agent not initialized; call an async method")
        return self._runtime

    async def run_message(self, message: str) -> Dict[str, Any]:
        await self._ensure_runtime()
        assert self._runtime is not None
        return await self._runtime.run_pipeline(message)

    async def handle(self, message: str) -> Dict[str, Any]:
        return await self.run_message(message)

    def get_registries(self) -> SystemRegistries:
        if self._runtime is None:
            raise RuntimeError("Agent not initialized")
        return self._runtime.registries
