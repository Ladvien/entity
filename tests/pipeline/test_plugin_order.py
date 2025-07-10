import yaml
from pipeline import PipelineStage
from entity.core.builder import _AgentBuilder
from entity.core.plugins import PromptPlugin


class First(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("first")
        context.set_metadata("order", order)
        _set_final_response(context)


class Second(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("second")
        context.set_metadata("order", order)


class Third(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        order = context.get_metadata("order") or []
        order.append("third")
        context.set_metadata("order", order)


def _set_final_response(context):
    order = context.get_metadata("order") or []
    context.set_response(order)


def test_builder_load_from_yaml_preserves_order(tmp_path):
    cfg = {
        "plugins": {
            "prompts": {
                "second": {"type": "test_plugin_order:Second"},
                "first": {"type": "test_plugin_order:First"},
                "third": {"type": "test_plugin_order:Third"},
            }
        }
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(cfg, sort_keys=False))

    builder = _AgentBuilder.from_yaml(str(path))
    plugins = builder.plugin_registry.get_plugins_for_stage(PipelineStage.DELIVER)
    assert [p.__class__ for p in plugins] == [Second, First, Third]
