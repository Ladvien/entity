from __future__ import annotations

"""CLI wrapper around :class:`PluginToolCLI` for quick scaffolding."""

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Type, cast

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_plugin_tool() -> ModuleType:
    """Load ``plugin_tool.py`` without relying on package imports."""
    path = ROOT / "src" / "cli" / "plugin_tool.py"
    spec = importlib.util.spec_from_file_location("plugin_tool", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    # Register module before execution to ensure imports resolve correctly
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_plugin_tool = _load_plugin_tool()
PluginToolCLI = cast(Type[Any], getattr(_plugin_tool, "PluginToolCLI"))
PLUGIN_TYPES = cast(Dict[str, Type[Any]], getattr(_plugin_tool, "PLUGIN_TYPES"))


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
        tool_cli = cast(Any, PluginToolCLI).__new__(PluginToolCLI)
        tool_cli.args = argparse.Namespace(
            name=self.args.name,
            type=self.args.type,
            out=self.args.out,
            docs_dir=self.args.docs_dir,
        )
        try:
            return cast(int, tool_cli._generate())
        except Exception as exc:  # pragma: no cover - CLI error path
            print(f"Error: {exc}")
            return 1


def main() -> None:
    cli = PluginCLI()
    raise SystemExit(cli.run())


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
