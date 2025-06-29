"""Example showing Agent.from_directory error handling."""

from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from pipeline import Agent  # noqa: E402


def main() -> None:
    agent = Agent.from_directory("../plugins")
    agent.run()


if __name__ == "__main__":
    main()
