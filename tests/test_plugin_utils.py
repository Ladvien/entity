import logging
from entity.core.plugins import Plugin  # noqa: F401 - configure plugins

from entity.core.plugins.utils import PluginAutoClassifier
from entity.core.stages import PipelineStage


async def very_long_function(context):
    x = 0
    x += 1
    x += 2
    x += 3
    x += 4
    x += 5
    x += 6
    x += 7
    x += 8
    x += 9
    x += 10
    x += 11
    x += 12
    x += 13
    x += 14
    x += 15
    x += 16
    x += 17
    x += 18
    x += 19
    x += 20
    return x


def test_warning_for_long_function(caplog):
    with caplog.at_level(logging.WARNING):
        PluginAutoClassifier.classify(
            very_long_function, {"stage": PipelineStage.THINK}
        )

    assert any("class-based plugin" in record.message for record in caplog.records)
