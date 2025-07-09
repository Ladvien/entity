"""Run a simple WebSocket server using the Entity framework.

Run with ``python -m examples.servers.websocket_server`` or install the package
in editable mode.
"""

from __future__ import annotations

import asyncio
import contextlib


from ..utilities import enable_plugins_namespace

enable_plugins_namespace()


def main() -> None:
    """Indicate that WebSocket support is not included."""

    print("WebSocket adapter not available in this build")


if __name__ == "__main__":
    main()
