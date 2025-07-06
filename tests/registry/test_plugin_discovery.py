import asyncio

from pipeline import PipelineStage, SystemInitializer


async def _run_initializer(cfg):
    initializer = SystemInitializer.from_dict(cfg)
    return await initializer.initialize()


def test_pyproject_discovery(tmp_path, monkeypatch):
    plugin_module = tmp_path / "my_plugin.py"
    plugin_module.write_text(
        """
from pipeline.base_plugins import PromptPlugin, ToolPlugin
from pipeline.stages import PipelineStage

class MyPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]
    async def _execute_impl(self, context):
        return None

class MyTool(ToolPlugin):
    async def execute_function(self, params):
        return "ok"
"""
    )

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.entity.plugins.prompts.test]
class = "my_plugin:MyPrompt"

[tool.entity.plugins.tools.echo]
class = "my_plugin:MyTool"
"""
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    cfg = {
        "plugin_dirs": [str(tmp_path)],
        "plugins": {"resources": {}, "tools": {}, "adapters": {}, "prompts": {}},
    }

    plugins, _, tools = asyncio.run(_run_initializer(cfg))
    think = plugins.get_plugins_for_stage(PipelineStage.THINK)
    assert any(p.__class__.__name__ == "MyPrompt" for p in think)
    assert tools.get("echo") is not None
