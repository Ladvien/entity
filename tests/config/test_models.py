from entity.config.models import PluginConfig
from entity.pipeline.stages import PipelineStage


def test_plugin_config_parsing():
    model = PluginConfig(type="x", stage="parse", dependencies=["db"])
    assert model.stage == PipelineStage.PARSE
    assert model.dependencies == ["db"]
    assert model.stages == []
