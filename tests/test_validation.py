import pytest

from entity.config.validation import (
    validate_config,
)
from entity.plugins import Plugin


class DummyPlugin(Plugin):
    stage = "think"

    class ConfigModel(Plugin.ConfigModel):
        value: int = 0

    async def _execute_impl(self, context):
        return "ok"


class MultiStagePlugin(Plugin):
    supported_stages = ["parse"]

    async def _execute_impl(self, context):
        return "ok"


def test_validate_config_success(tmp_path):
    cfg = tmp_path / "conf.yml"
    cfg.write_text("resources: {}\nworkflow: {}")
    data = validate_config(cfg)
    assert data.resources == {}
    assert data.workflow == {}


def test_validate_config_missing(tmp_path):
    cfg = tmp_path / "bad.yml"
    cfg.write_text("workflow: {}")
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_plugin_config_validation():
    class TestPlugin(Plugin):
        supported_stages = ["think"]

        class ConfigModel(Plugin.ConfigModel):
            value: int

        async def _execute_impl(self, context):
            return "ok"

    plugin_instance = TestPlugin({}, config={"value": "bad"})
    result = plugin_instance.validate_config()
    assert not result.success
    assert "value" in result.errors[0]