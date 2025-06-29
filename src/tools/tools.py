class ToolManager:
    """Simplified tool manager used for tests."""

    def __init__(self, config=None):
        self.config = config
        self._tools = {}

    def register_class(self, cls):
        instance = cls()
        if hasattr(instance, "use_registry"):
            instance.use_registry = False
        self._tools[instance.name] = instance

    def get_tool(self, name):
        return self._tools.get(name)

    def list_tool_names(self):
        return list(self._tools.keys())
