"""Run a simple CLI adapter using the Entity framework.

Run with ``python -m examples.servers.cli_adapter`` or install the package in
editable mode.
"""

from __future__ import annotations


from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

import asyncio

from plugins.builtin.adapters.cli import CLIAdapter

from pipeline import PipelineManager
from pipeline.initializer import SystemInitializer


async def main() -> None:
    initializer = SystemInitializer.from_yaml("config/dev.yaml")
    registries = await initializer.initialize()
    manager = PipelineManager(registries)
    adapter = CLIAdapter(manager)
    await adapter.serve(registries)


if __name__ == "__main__":
    asyncio.run(main())
