class Agent:
    def __init__(self, resources=None, workflow=None, infrastructure=None):
        self.resources = resources or {}
        self.workflow = workflow
        self.infrastructure = infrastructure

    async def chat(self, message, user_id="default"):
        """Echo the given message back in a response dict."""
        return {"response": message}
