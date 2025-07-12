import logging
import sys
from pathlib import Path

import pytest

SRC = str(Path(__file__).resolve().parents[1] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    from cli.plugin_tool.main import PluginToolArgs, PluginToolCLI
except ModuleNotFoundError:  # pragma: no cover - env dependent
    pytest.skip("cli package not available", allow_module_level=True)


def _create_tmp_plugin(tmp_path):
    file = tmp_path / "sample.py"
    file.write_text("""async def foo(ctx):\n    return 'hi'\n""")
    return file


def test_analyze_plugin_reports_reason(tmp_path, caplog):
    path = _create_tmp_plugin(tmp_path)
    cli = PluginToolCLI.__new__(PluginToolCLI)
    cli.args = PluginToolArgs(command="analyze-plugin", path=str(path))
    caplog.set_level(logging.INFO)
    result = cli._analyze_plugin()
    assert result == 0
    messages = [r.message for r in caplog.records if "foo ->" in r.message]
    assert messages
    assert "source heuristics" in messages[0]
