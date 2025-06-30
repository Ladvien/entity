import logging

from entity import Agent
from pipeline import PipelineStage


def test_from_directory_import_error(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    good = tmp_path / "good.py"
    good.write_text(
        """\n
async def hi_plugin(ctx):\n    return 'hi'\n"""
    )

    bad = tmp_path / "bad.py"
    bad.write_text("import nonexistent_module")

    agent = Agent.from_directory(str(tmp_path))
    plugins = agent.plugins.get_for_stage(PipelineStage.DO)
    assert any(p.name == "hi_plugin" for p in plugins)
    assert not any(p.name == "bad" for p in plugins)
    assert any("Failed to import plugin module" in r.message for r in caplog.records)


def test_directory_plugin_naming(tmp_path):
    mixed = tmp_path / "mixed.py"
    mixed.write_text(
        """
from pipeline import BasePlugin, PipelineStage

async def good_plugin(ctx):
    return 'ok'

def bad(ctx):
    return 'no'

class GoodClass(BasePlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        return 'class'

class BadClass:
    pass
"""
    )

    agent = Agent.from_directory(str(tmp_path))
    plugins = agent.plugins.get_for_stage(PipelineStage.DO)

    names = {getattr(p, "name", p.__class__.__name__) for p in plugins}
    classes = {p.__class__.__name__ for p in plugins}

    assert "good_plugin" in names
    assert "bad" not in names
    assert "GoodClass" in classes
    assert "BadClass" not in classes
