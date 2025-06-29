import logging

from pipeline import Agent, PipelineStage


def test_from_directory_import_error(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    good = tmp_path / "good.py"
    good.write_text(
        """\n
def hi_plugin(ctx):\n    return 'hi'\n"""
    )

    bad = tmp_path / "bad.py"
    bad.write_text("import nonexistent_module")

    agent = Agent.from_directory(str(tmp_path))
    plugins = agent.plugins.get_for_stage(PipelineStage.DO)
    assert any(p.name == "hi_plugin" for p in plugins)
    assert not any(p.name == "bad" for p in plugins)
    assert any("Failed to import plugin module" in r.message for r in caplog.records)
