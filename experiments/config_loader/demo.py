from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from .loader import ConfigWatcher


async def main() -> None:
    os.environ.setdefault("GREETING", "Hello, world!")
    cfg_file = Path(__file__).with_name("config.yaml")

    def on_update(cfg: dict[str, Any]) -> None:
        print("Config reloaded:", cfg)

    watcher = ConfigWatcher(cfg_file)
    watcher.start(on_update)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
