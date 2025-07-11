import logging

from cli.plugin_tool.main import PluginToolArgs, PluginToolCLI


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
