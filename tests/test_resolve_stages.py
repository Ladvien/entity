import logging

from pipeline.utils import resolve_stages
from pipeline.stages import PipelineStage


def test_resolve_stages_config_explicit():
    stages, explicit = resolve_stages(
        "MyPlugin",
        cfg_value=PipelineStage.DO,
        attr_stages=[],
        explicit_attr=False,
        type_defaults=[PipelineStage.THINK],
        ensure_stage=PipelineStage.ensure,
        logger=logging.getLogger(__name__),
        error_type=ValueError,
    )
    assert stages == [PipelineStage.DO]
    assert explicit


def test_resolve_stages_auto_inferred():
    stages, explicit = resolve_stages(
        "MyPlugin",
        cfg_value=None,
        attr_stages=[PipelineStage.THINK],
        explicit_attr=False,
        type_defaults=[],
        ensure_stage=PipelineStage.ensure,
        logger=logging.getLogger(__name__),
        auto_inferred=True,
        error_type=ValueError,
    )
    assert stages == [PipelineStage.THINK]
    assert not explicit
