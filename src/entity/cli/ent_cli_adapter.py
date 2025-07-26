from __future__ import annotations

import asyncio
import signal
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel

from entity.plugins.input_adapter import InputAdapterPlugin
from entity.plugins.output_adapter import OutputAdapterPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.plugins.context import PluginContext
from entity.resources.logging import LogCategory, LogLevel


class EntCLIAdapter(InputAdapterPlugin, OutputAdapterPlugin):
    """Simple CLI adapter using stdin and stdout with signal handling."""

    # TODO: Consider separate classes for input and output adapters.
    supported_stages = [WorkflowExecutor.INPUT, WorkflowExecutor.OUTPUT]

    def __init__(
        self, resources: dict[str, Any], config: dict[str, Any] | None = None
    ) -> None:
        super().__init__(resources, config)
        self._stop = asyncio.Event()
        self.console = Console()

    def stop(self) -> None:
        """Signal any waiting ``wait_closed`` calls to exit."""
        self._stop.set()

    def _install_signals(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._stop.set)
            except NotImplementedError:  # pragma: no cover - windows fallback
                signal.signal(sig, lambda _s, _f: self._stop.set())

    async def _read_line(self) -> str:
        return await asyncio.to_thread(self.console.input, "[bold cyan]> [/]")

    async def _execute_impl(self, context: PluginContext) -> str:
        self._install_signals()
        logger = context.get_resource("logging")
        try:
            if context.current_stage == WorkflowExecutor.INPUT:
                return await self._handle_input(context)
            if context.current_stage == WorkflowExecutor.OUTPUT:
                return await self._handle_output(context)
        except Exception as exc:  # pragma: no cover - runtime safety
            if logger is not None:
                await logger.log(
                    LogLevel.ERROR,
                    LogCategory.ERROR,
                    "CLI adapter error",
                    error=str(exc),
                )
            self.console.print(Panel(str(exc), title="Error", style="red"))
            raise

        return context.message or ""

    async def _handle_input(self, context: PluginContext) -> str:
        """Prompt the user for input."""

        line = await self._read_line()
        if not line:
            self._stop.set()
            raise KeyboardInterrupt

        message = line.rstrip("\n")
        await context.remember("cli_input", message)
        return message

    async def _handle_output(self, context: PluginContext) -> str:
        """Write ``context.response`` to stdout using Rich."""

        output = context.response or context.message or ""
        try:
            self.console.print(Panel(output, title="Response", style="green"))
        except BrokenPipeError:
            self._stop.set()
        else:
            self._stop.set()
        context.say(output)
        return output

    async def wait_closed(self) -> None:
        await self._stop.wait()
