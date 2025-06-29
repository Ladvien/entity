class ResourceRegistry:
    def __init__(self) -> None:
        self._resources = {}

    def add_resource(self, resource) -> None:
        self._resources[resource.name] = resource

    def get(self, name: str):
        return self._resources.get(name)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools = {}

    def add_tool(self, tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str):
        return self._tools.get(name)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins_by_stage = {}

    def register_plugin_for_stage(self, plugin, stage, name: str) -> None:
        self._plugins_by_stage.setdefault(stage, []).append(plugin)

    def get_for_stage(self, stage):
        return self._plugins_by_stage.get(stage, [])
