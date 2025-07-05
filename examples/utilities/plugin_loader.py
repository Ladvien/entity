"""Example showing Agent.from_directory error handling."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from utilities import enable_plugins_namespace

enable_plugins_namespace()

from plugins.builtin.adapters.server import AgentServer  # noqa: E402

from entity import Agent  # noqa: E402


def main() -> None:
    agent = Agent.from_directory("../plugins")
    runtime = agent.builder.build_runtime()
    server = AgentServer(runtime)
    server.run_http()


if __name__ == "__main__":
    main()
