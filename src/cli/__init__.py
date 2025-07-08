"""Expose the CLI helpers for tests and entry points."""

import sys
from importlib import util
from pathlib import Path

_cli_path = Path(__file__).resolve().parent.parent / "cli.py"
_spec = util.spec_from_file_location("_entity_cli", _cli_path)
_module = util.module_from_spec(_spec)
if _spec.loader is None:  # pragma: no cover - sanity check
    raise RuntimeError("Failed to load CLI module")
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

CLI = _module.CLI
main = _module.main

__all__ = ["CLI", "main"]
