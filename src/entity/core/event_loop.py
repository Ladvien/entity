from entity.core.context import EventContext
from entity.core.pipeline import PluginPipeline


class EventLoop:
    def __init__(self, plugin_graph, resource_registry):
        self.plugin_graph = plugin_graph
        self.resources = resource_registry

    async def handle_request(self, request: dict):
        context = EventContext(request=request, resources=self.resources)

        for stage, plugins in self.plugin_graph.stages.items():
            pipeline = PluginPipeline(plugins)
            await pipeline.run(context)

            if context.recompile:
                break

        return context.response
