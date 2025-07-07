import asyncio

from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      PromptPlugin, SystemRegistries, ToolRegistry,
                      ValidationResult, execute_pipeline,
                      update_plugin_configuration)
from pipeline.resources import ResourceContainer


class TestReconfigPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    name = "test_plugin"

    async def _execute_impl(self, context):
        pass

    @classmethod
    def validate_config(cls, config):
        if "value" not in config:
            return ValidationResult.error_result("missing value")
        return ValidationResult.success_result()

    async def _handle_reconfiguration(self, old_config, new_config):
        self.updated_to = new_config["value"]


class SlowPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        await asyncio.sleep(0.2)


async def make_registry(add_slow: bool = False):
    reg = PluginRegistry()
    plugin = TestReconfigPlugin({"value": "one"})
    await reg.register_plugin_for_stage(plugin, PipelineStage.THINK)
    if add_slow:
        await reg.register_plugin_for_stage(SlowPlugin(), PipelineStage.THINK)
    return reg, plugin


def test_update_plugin_configuration_success():
    reg, plugin = asyncio.run(make_registry())
    result = asyncio.run(
        update_plugin_configuration(reg, "test_plugin", {"value": "two"})
    )
    assert result.success
    assert plugin.config["value"] == "two"
    assert plugin.updated_to == "two"


def test_update_plugin_configuration_restart_required():
    class NRPlugin(TestReconfigPlugin):
        def supports_runtime_reconfiguration(self) -> bool:
            return False

    reg = PluginRegistry()
    p = NRPlugin({"value": "x"})
    asyncio.run(reg.register_plugin_for_stage(p, PipelineStage.THINK))
    result = asyncio.run(
        update_plugin_configuration(reg, "test_plugin", {"value": "y"})
    )
    assert result.success
    assert p.config["value"] == "y"


def test_update_waits_for_running_pipeline():
    async def run_test():
        reg, plugin = await make_registry(add_slow=True)
        registries = SystemRegistries(ResourceContainer(), ToolRegistry(), reg)
        manager = PipelineManager()
        task = asyncio.create_task(
            execute_pipeline("hello", registries, pipeline_manager=manager)
        )
        await asyncio.sleep(0.05)
        start = asyncio.get_event_loop().time()
        result = await update_plugin_configuration(
            reg,
            "test_plugin",
            {"value": "two"},
            pipeline_manager=manager,
        )
        duration = asyncio.get_event_loop().time() - start
        await task
        return result, duration, plugin

    result, duration, plugin = asyncio.run(run_test())
    assert result.success
    assert duration >= 0.2
    assert plugin.updated_to == "two"


def test_dependency_conflict_triggers_rollback():
    class DependentPlugin(PromptPlugin):
        stages = [PipelineStage.THINK]
        dependencies = ["test_plugin"]

        async def _execute_impl(self, context):
            pass

        async def on_dependency_reconfigured(self, name, old, new):
            return new["value"] != "bad"

    async def run_test():
        reg = PluginRegistry()
        plugin = TestReconfigPlugin({"value": "one"})
        dep = DependentPlugin()
        await reg.register_plugin_for_stage(plugin, PipelineStage.THINK)
        await reg.register_plugin_for_stage(dep, PipelineStage.THINK)
        result = await update_plugin_configuration(reg, "test_plugin", {"value": "bad"})
        return result, plugin

    result, plugin = asyncio.run(run_test())
    assert not result.success
    assert plugin.config["value"] == "one"
    assert plugin.config_version == 1


def test_rollback_to_previous_version():
    async def run_test():
        reg, plugin = await make_registry()
        await update_plugin_configuration(reg, "test_plugin", {"value": "two"})
        await update_plugin_configuration(reg, "test_plugin", {"value": "three"})
        await plugin.rollback_config(2)
        return plugin

    plugin = asyncio.run(run_test())
    assert plugin.config_version == 2
    assert plugin.config["value"] == "two"
