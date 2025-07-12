import logging

from entity import Agent
from pipeline import PipelineStage


def test_from_package_import_error(tmp_path, caplog, monkeypatch):
    caplog.set_level(logging.ERROR)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "good.py").write_text(
        "from entity.core.decorators import plugin\n"
        "from pipeline import PipelineStage\n"
        "@plugin(stage=PipelineStage.DO)\n"
        "async def ok_plugin(ctx):\n    return 'ok'\n"
    )
    (pkg / "bad.py").write_text("import nonexistent_module")

    monkeypatch.syspath_prepend(str(tmp_path))
    agent = Agent.from_package("pkg")
    plugins = agent.builder.plugin_registry.get_plugins_for_stage(PipelineStage.DO)
    assert any(p.name == "ok_plugin" for p in plugins)
    assert not any(p.name == "bad" for p in plugins)
    assert any("Failed to import plugin module" in r.message for r in caplog.records)


def test_package_plugin_naming(tmp_path, monkeypatch):
    pkg = tmp_path / "pkg2"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (sub / "__init__.py").write_text("")

    (pkg / "mods.py").write_text(
        """
from pipeline import BasePlugin, PipelineStage
from entity.core.decorators import plugin

@plugin(stage=PipelineStage.DO)
async def top_plugin(ctx):
    return 'top'

class TopClass(Plugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        return 'class'

class BadClass:
    pass
"""
    )

    (sub / "submod.py").write_text(
        """
from entity.core.decorators import plugin
from pipeline import PipelineStage

@plugin(stage=PipelineStage.DO)
async def sub_plugin(ctx):
    return 'sub'
"""
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    agent = Agent.from_package("pkg2")
    plugins = agent.builder.plugin_registry.get_plugins_for_stage(PipelineStage.DO)

    names = {getattr(p, "name", p.__class__.__name__) for p in plugins}
    classes = {p.__class__.__name__ for p in plugins}

    assert "top_plugin" in names
    assert "sub_plugin" in names
    assert "TopClass" in classes
    assert "BadClass" not in classes
