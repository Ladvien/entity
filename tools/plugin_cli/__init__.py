from __future__ import annotations

"""CLI wrapper around :class:`PluginToolCLI` for quick scaffolding."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cli.plugin_tool import PLUGIN_TYPES, PluginToolCLI  # type: ignore


class PluginCLI:
    """Create plugin modules from predefined templates."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Scaffold a new plugin")
        parser.add_argument("name", help="Plugin module name")
        parser.add_argument("--type", choices=list(PLUGIN_TYPES), default="tool")
        parser.add_argument("--out", default="user_plugins")
        parser.add_argument("--docs-dir", default="docs/source")
        return parser.parse_args()

    def run(self) -> int:
        tool_cli = PluginToolCLI.__new__(PluginToolCLI)
        tool_cli.args = argparse.Namespace(
            name=self.args.name,
            type=self.args.type,
            out=self.args.out,
            docs_dir=self.args.docs_dir,
        )
        try:
            return tool_cli._generate()
        except Exception as exc:  # pragma: no cover - CLI error path
            print(f"Error: {exc}")
            return 1


def main() -> None:
    cli = PluginCLI()
    raise SystemExit(cli.run())


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
