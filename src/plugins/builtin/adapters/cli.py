from __future__ import annotations

"""Command-line adapter for interactive pipeline usage.

This module defines :class:`CLIAdapter`, an adapter that exposes the
pipeline through an interactive REPL style prompt. Users can type a
message, the pipeline processes it, and the resulting response is
printed to standard output.
"""

import asyncio
from typing import Any, cast

from pipeline.base_plugins import AdapterPlugin
from pipeline.exceptions import ResourceError
from pipeline.manager import PipelineManager
from pipeline.pipeline import execute_pipeline
from pipeline.security import AdapterAuthenticator
from pipeline.stages import PipelineStage
from registry import SystemRegistries


class CLIAdapter(AdapterPlugin):
    """Interactive command line adapter."""

    # Provide a placeholder pipeline stage to satisfy BasePlugin's
    # subclass checks. Adapters operate outside the pipeline stages.
    stages: list[PipelineStage] = [PipelineStage.PARSE]

    def __init__(
        self,
        manager: PipelineManager | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(config)
        self.manager = manager
        tokens_cfg = self.config.get("auth_tokens", [])
        if isinstance(tokens_cfg, list):
            mapping = {t: ["cli"] for t in tokens_cfg}
        else:
            mapping = {str(k): v for k, v in dict(tokens_cfg).items()}
        self.authenticator = AdapterAuthenticator(mapping)
        self._registries: SystemRegistries | None = None

    async def serve(self, registries: SystemRegistries) -> None:
        """Run the interactive command-line loop.

        Parameters
        ----------
        registries:
            System registries containing all initialized plugins and resources.
        """
        self._registries = registries
        if self.authenticator._tokens:
            token = await asyncio.to_thread(input, "Token: ")
            if not self.authenticator.authenticate(
                token
            ) or not self.authenticator.authorize(token, "cli"):
                self.logger.error("Unauthorized")
                return
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
                    raise ResourceError("Adapter not initialized")
                response = cast(
                    dict[str, Any],
                    await execute_pipeline(message, self._registries),
                )
            self.logger.info("%s", response)

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
