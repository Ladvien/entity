from entity import Agent
from pipeline import PipelineStage, PromptPlugin


def test_plugin_decorator_registration():
    agent = Agent()

    @agent.plugin
    async def hello(context):
        return "hi"

    do_plugins = agent.plugin_registry.get_plugins_for_stage(PipelineStage.DO)
    assert any(p.name == "hello" for p in do_plugins)


class ExamplePlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        pass


def test_add_plugin():
    agent = Agent()
    plugin = ExamplePlugin()
    agent.add_plugin(plugin)
    think_plugins = agent.plugin_registry.get_plugins_for_stage(PipelineStage.THINK)
    assert plugin in think_plugins
