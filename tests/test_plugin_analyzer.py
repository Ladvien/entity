import logging


from pipeline import Plugin  # noqa: F401 - triggers plugin configuration

from entity.core.decorators import plugin
from entity.core.stages import PipelineStage


def test_warning_logged_for_complex_function(caplog):
    async def complex_func(context):
        for i in range(5):
            if i > 2:
                break

    with caplog.at_level(logging.WARNING):
        plugin(stage=PipelineStage.THINK)(complex_func)

    assert any("consider" in record.message for record in caplog.records)
