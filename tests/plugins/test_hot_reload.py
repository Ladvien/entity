import pytest

from entity.core.plugins import Plugin
from entity.core.registries import PluginRegistry
from entity.pipeline.config.config_update import update_plugin_configuration
from entity.pipeline.stages import PipelineStage


class ConfigPlugin(Plugin):
    name = "cfg"
    stages = [PipelineStage.THINK]

    def __init__(self, config=None):
        super().__init__(config or {})
        self.value = self.config.get("value", 0)

    async def _execute_impl(self, context):
        return self.value

    async def _handle_reconfiguration(self, old, new):
        self.value = new.get("value", 0)


class DepPlugin(Plugin):
    stages = [PipelineStage.THINK]
    dependencies = ["cfg"]

    def __init__(self, cfg=None):
        super().__init__(cfg or {})
        self.seen = None

    async def _execute_impl(self, context):
        return "dep"

    async def on_dependency_reconfigured(self, name, old, new):
        self.seen = new.get("value")
        return True


class RejectPlugin(DepPlugin):
    stages = [PipelineStage.THINK]

    async def on_dependency_reconfigured(self, name, old, new):
        return False


@pytest.mark.asyncio
async def test_update_notifies_dependents():
    registry = PluginRegistry()
    base = ConfigPlugin({"value": 1})
    dep = DepPlugin()
    await registry.register_plugin_for_stage(base, str(PipelineStage.THINK), "cfg")
    await registry.register_plugin_for_stage(dep, str(PipelineStage.THINK), "dep")

    result = await update_plugin_configuration(registry, "cfg", {"value": 2})
    assert result.success
    assert base.value == 2
    assert dep.seen == 2
    assert base.config_version == 2


@pytest.mark.asyncio
async def test_update_rolls_back_on_rejection():
    registry = PluginRegistry()
    base = ConfigPlugin({"value": 1})
    dep = RejectPlugin()
    await registry.register_plugin_for_stage(base, str(PipelineStage.THINK), "cfg")
    await registry.register_plugin_for_stage(dep, str(PipelineStage.THINK), "dep")

    result = await update_plugin_configuration(registry, "cfg", {"value": 2})
    assert not result.success and not result.requires_restart
    assert base.value == 1
    assert base.config_version == 1


@pytest.mark.asyncio
async def test_update_rejects_type_change():
    registry = PluginRegistry()
    base = ConfigPlugin({"value": 1})
    await registry.register_plugin_for_stage(base, str(PipelineStage.THINK), "cfg")

    result = await update_plugin_configuration(
        registry,
        "cfg",
        {"value": 1, "type": "some.other:Class"},
    )
    assert not result.success and result.requires_restart


class FailingRollbackPlugin(DepPlugin):
    stages = [PipelineStage.THINK]

    def __init__(self, config=None):
        super().__init__(config or {})
        self.value = self.config.get("value", 0)

    async def _execute_impl(self, context):
        return self.value

    async def _handle_reconfiguration(self, old, new):
        self.value = new.get("value", 0)

    async def rollback_config(self, version: int) -> None:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_update_handles_failed_rollback():
    registry = PluginRegistry()
    base = FailingRollbackPlugin({"value": 1})
    dep = RejectPlugin()
    await registry.register_plugin_for_stage(base, str(PipelineStage.THINK), "cfg")
    await registry.register_plugin_for_stage(dep, str(PipelineStage.THINK), "dep")

    result = await update_plugin_configuration(registry, "cfg", {"value": 2})
    assert not result.success and not result.requires_restart
    assert base.value == 2
    assert base.config_version == 2
