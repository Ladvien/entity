"""Run a simple CLI adapter using the Entity framework.

Run with ``python -m examples.servers.cli_adapter`` or install the package in
editable mode.
"""

from __future__ import annotations


from ..utilities import enable_plugins_namespace

enable_plugins_namespace()

import asyncio


def main() -> None:
    """Indicate that CLI adapter is not available."""

    print("CLI adapter example requires optional components")


if __name__ == "__main__":
    main()
