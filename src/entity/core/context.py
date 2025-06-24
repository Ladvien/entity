from entity.types.context_models import ResourceRegistry


class EventContext:
    def __init__(self, request, metadata=None, resources=None):
        self.request = request
        self.response = None
        self.prompt = ""
        self.memory_context = ""
        self.metadata = metadata or {}
        self.recompile = False
        self.resources = resources or ResourceRegistry()
