from pipeline.base_plugins import AdapterPlugin, PromptPlugin, ToolPlugin
from pipeline.stages import PipelineStage


class MyTool(ToolPlugin):
    async def execute_function(self, params):
        return params


class MyPrompt(PromptPlugin):
    async def _execute_impl(self, context):
        pass


class MyAdapter(AdapterPlugin):
    async def _execute_impl(self, context):
        pass


def test_tool_plugin_default_stage():
    assert MyTool.stages == [PipelineStage.DO]


def test_prompt_plugin_default_stage():
    assert MyPrompt.stages == [PipelineStage.THINK]


def test_adapter_plugin_default_stage():
    assert MyAdapter.stages == [PipelineStage.PARSE, PipelineStage.DELIVER]
