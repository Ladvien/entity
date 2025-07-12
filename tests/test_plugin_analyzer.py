import logging


from entity.pipeline import Plugin  # noqa: F401 - triggers plugin configuration

from entity.core.decorators import plugin
from entity.core.stages import PipelineStage


def test_warning_logged_for_complex_function(caplog):
    async def complex_func(context):
        total = 0
        for i in range(5):
            if i > 2:
                break
            total += i
        for j in range(3):
            total += j
        for k in range(3):
            total += k
        for l in range(3):
            total += l
        for m in range(3):
            total += m
        for n in range(3):
            total += n
        for o in range(3):
            total += o
        for p in range(3):
            total += p
        for q in range(3):
            total += q
        for r in range(3):
            total += r
        return total

    with caplog.at_level(logging.WARNING):
        plugin(stage=PipelineStage.THINK)(complex_func)

    assert any("consider" in record.message for record in caplog.records)
