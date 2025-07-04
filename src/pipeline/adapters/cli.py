from __future__ import annotations

"""Command-line adapter for interactive pipeline usage.

This module defines :class:`CLIAdapter`, an adapter that exposes the
pipeline through an interactive REPL style prompt. Users can type a
message, the pipeline processes it, and the resulting response is
printed to standard output.
"""

import asyncio
from typing import Any, cast

from registry import SystemRegistries

from ..manager import PipelineManager
from ..pipeline import execute_pipeline
from ..stages import PipelineStage
from ..user_plugins import AdapterPlugin


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
        """Run the interactive command-line loop.

        Parameters
        ----------
        registries:
            System registries containing all initialized plugins and resources.
        """
        self._registries = registries
        self.logger.info("Enter message (Ctrl-D to quit)")
        while True:
            try:
                message = await asyncio.to_thread(input, "> ")
            except EOFError:
                self.logger.info("Exiting CLI")
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
            self.logger.info("%s", response)
            print(response)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
