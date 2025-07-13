import logging
from entity.cli.plugin_tool.main import PluginToolCLI, PluginToolArgs


def _make_cli(path: str) -> PluginToolCLI:
    cli = PluginToolCLI.__new__(PluginToolCLI)
    cli.args = PluginToolArgs(command="test", path=path)
    return cli


def test_test_command_runs_pipeline(tmp_path, caplog):
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text(
        "from entity.core.plugins import Plugin\n"
        "from entity.pipeline.stages import PipelineStage\n\n"
        "class Demo(Plugin):\n"
        "    stages=[PipelineStage.OUTPUT]\n"
        "    async def _execute_impl(self, ctx):\n"
        '        ctx.say("ok")\n'
    )
    cli = _make_cli(str(plugin_file))
    with caplog.at_level(logging.INFO):
        result = cli._test()
    assert result == 0
    log = "\n".join(r.message for r in caplog.records)
    assert "Pipeline result" in log


def test_test_command_tool_plugin(tmp_path, caplog):
    plugin_file = tmp_path / "tool.py"
    plugin_file.write_text(
        "from entity.core.plugins import ToolPlugin\n"
        "class Demo(ToolPlugin):\n"
        "    async def execute_function(self, params):\n"
        "        return 'ok'\n"
    )
    cli = _make_cli(str(plugin_file))
    with caplog.at_level(logging.INFO):
        result = cli._test()
    assert result == 0
    log = "\n".join(r.message for r in caplog.records)
    assert "tool function" in log
