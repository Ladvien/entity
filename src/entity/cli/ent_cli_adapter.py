from __future__ import annotations

import asyncio
import signal
import sys
from typing import Any

from entity.plugins.input_adapter import InputAdapterPlugin
from entity.plugins.output_adapter import OutputAdapterPlugin
from entity.workflow.executor import WorkflowExecutor
from entity.plugins.context import PluginContext


class EntCLIAdapter(InputAdapterPlugin, OutputAdapterPlugin):
    """Simple CLI adapter using stdin and stdout with signal handling."""

    # TODO: Consider separate classes for input and output adapters.
    supported_stages = [WorkflowExecutor.INPUT, WorkflowExecutor.OUTPUT]

    def __init__(
        self, resources: dict[str, Any], config: dict[str, Any] | None = None
    ) -> None:
        super().__init__(resources, config)
        self._stop = asyncio.Event()

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
        return await asyncio.to_thread(sys.stdin.readline)

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
                await logger.log("error", "cli_error", error=str(exc))
            raise

        return context.message or ""

    async def _handle_input(self, context: PluginContext) -> str:
        """Read a single line from stdin."""

        line = await self._read_line()
        if not line:
            self._stop.set()
            raise KeyboardInterrupt

        message = line.rstrip("\n")
        await context.remember("cli_input", message)
        return message

    async def _handle_output(self, context: PluginContext) -> str:
        """Write ``context.response`` to stdout."""

        output = context.response or context.message or ""
        try:
            print(output)
        except BrokenPipeError:
            self._stop.set()
        else:
            # ensure CLI exits after successfully writing output
            self._stop.set()
        context.say(output)
        return output

    async def wait_closed(self) -> None:
        await self._stop.wait()
