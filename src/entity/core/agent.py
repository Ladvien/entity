# TODO: Use absolute imports
from entity.defaults import load_defaults
from entity.plugins.defaults import default_workflow
from entity.workflow import WorkflowExecutor


class Agent:
    # TODO: Arguments should have typehints
    def __init__(self, resources=None, workflow=None, infrastructure=None):
        self.resources = resources or load_defaults()
        self.workflow = workflow
        self.infrastructure = infrastructure

    async def chat(self, message: str, user_id: str = "default"):
        """Process ``message`` through the workflow for ``user_id``."""

        steps = self.workflow or default_workflow()
        if isinstance(steps, dict):
            workflow_steps = steps
        else:
            workflow_steps = {
                stage: [plugin] for stage, plugin in zip(WorkflowExecutor._ORDER, steps)
            }

        executor = WorkflowExecutor(self.resources, workflow_steps)
        result = await executor.run(message, user_id=user_id)
        # TODO: Use a response object instead of a dict
        return {"response": result}
