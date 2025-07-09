import logging

from pipeline import PipelineStage, PromptPlugin, SystemInitializer


def test_config_overrides_class_warning(caplog):
    class MyPrompt(PromptPlugin):
        stages = [PipelineStage.THINK]

        async def _execute_impl(self, context):
            pass

    initializer = SystemInitializer()
    plugin = MyPrompt({})
    caplog.set_level(logging.WARNING, logger="pipeline.initializer")
    logging.getLogger("pipeline.initializer").addHandler(caplog.handler)
    stages, _ = initializer._resolve_plugin_stages(
        MyPrompt, plugin, {"stage": PipelineStage.DO}
    )
    assert stages == [PipelineStage.DO]
    assert any(
        "override class stages" in record.getMessage()
        and "MyPrompt" in record.getMessage()
        for record in caplog.records
    )
