"""Example showing Agent.from_directory error handling."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from . import enable_plugins_namespace

enable_plugins_namespace()

from entity import Agent  # noqa: E402
from plugins.builtin.adapters.server import AgentServer  # noqa: E402


def main() -> None:
    base_path = pathlib.Path(__file__).resolve().parents[2]
    plugins_dir = base_path / "src" / "plugins"
    agent = Agent.from_directory(str(plugins_dir))
    runtime = agent.builder.build_runtime()
    server = AgentServer(runtime)
    server.run_http()


if __name__ == "__main__":
    main()
