from ..defaults import load_defaults
from ..plugins.defaults import default_workflow


class Agent:
    def __init__(self, resources=None, workflow=None, infrastructure=None):
        self.resources = resources or load_defaults()
        self.workflow = workflow
        self.infrastructure = infrastructure

    async def chat(self, message, user_id="default"):
        """Process the message through the configured workflow."""

        steps = self.workflow or default_workflow()
        result = message
        for plugin_cls in steps:
            plugin = plugin_cls(self.resources)
            result = await plugin.run(result, user_id)

        return {"response": result}
