class PluginPipeline:
    def __init__(self, plugins):
        self.plugins = plugins

    async def run(self, context):
        for plugin in self.plugins:
            await plugin.handle(context)
