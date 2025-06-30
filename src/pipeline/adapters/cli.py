from __future__ import annotations

import asyncio
from typing import Any, cast

from ..manager import PipelineManager
from ..pipeline import execute_pipeline
from ..plugins import AdapterPlugin
from ..registries import SystemRegistries
from ..stages import PipelineStage


class CLIAdapter(AdapterPlugin):
    """Interactive command line adapter."""

    stages = [PipelineStage.DELIVER]

    def __init__(
        self,
        manager: PipelineManager | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(config)
        self.manager = manager
        self._registries: SystemRegistries | None = None

    async def serve(self, registries: SystemRegistries) -> None:
        """Start interactive prompt loop."""
        self._registries = registries
        print("Enter message (Ctrl-D to quit)")
        while True:
            try:
                message = await asyncio.to_thread(input, "> ")
            except EOFError:
                print()
                break
            message = message.strip()
            if not message:
                continue
            if self.manager is not None:
                response = await self.manager.run_pipeline(message)
            else:
                if self._registries is None:
                    raise RuntimeError("Adapter not initialized")
                response = cast(
                    dict[str, Any],
                    await execute_pipeline(message, self._registries),
                )
            print(response)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
