import logging
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from cli.plugin_tool.main import PluginToolCLI, PluginToolArgs


def _make_cli(path: str) -> PluginToolCLI:
    cli = PluginToolCLI.__new__(PluginToolCLI)
    cli.args = PluginToolArgs(command="analyze-plugin", path=path)
    return cli


def test_analyze_plugin_accept_defaults(tmp_path, monkeypatch, caplog):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text("""async def func(ctx):\n    pass\n""")

    cli = _make_cli(str(plugin_file))
    monkeypatch.setattr("builtins.input", lambda *_: "")

    with caplog.at_level(logging.INFO):
        cli._analyze_plugin()

    log = "\n".join(r.message for r in caplog.records)
    assert "plugins:" in log
    assert "prompts" in log
    assert "think" in log


def test_analyze_plugin_override(tmp_path, monkeypatch, caplog):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text("""async def func(ctx):\n    pass\n""")

    cli = _make_cli(str(plugin_file))
    monkeypatch.setattr("builtins.input", lambda *_: "parse,deliver")

    with caplog.at_level(logging.INFO):
        cli._analyze_plugin()

    log = "\n".join(r.message for r in caplog.records)
    assert "input" in log
    assert "output" in log
