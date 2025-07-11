import logging
import sys
from importlib import util
from pathlib import Path

module_name = "cli.plugin_tool.main"
module_path = Path(__file__).resolve().parents[1] / "src/cli/plugin_tool/main.py"
spec = util.spec_from_file_location(
    module_name, module_path, submodule_search_locations=[str(module_path.parent)]
)
plugin_module = util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[module_name] = plugin_module
spec.loader.exec_module(plugin_module)
PluginToolArgs = plugin_module.PluginToolArgs
PluginToolCLI = plugin_module.PluginToolCLI


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
