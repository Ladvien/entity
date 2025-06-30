"""Run a simple HTTP server using the Entity framework."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from entity import Agent


def main() -> None:
    agent = Agent({"server": {"host": "127.0.0.1", "port": 8000}})  # type: ignore[arg-type]
    agent.run()


if __name__ == "__main__":
    main()
