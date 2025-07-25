# TODO: Use absolute imports
from pathlib import Path

from entity.defaults import load_defaults
from entity.plugins.defaults import default_workflow
from entity.workflow import WorkflowExecutor
from entity.workflow.templates import load_template, TemplateNotFoundError
from entity.workflow.workflow import Workflow
from entity.config import load_config


class Agent:
    # TODO: Arguments should have typehints
    def __init__(self, resources=None, workflow=None, infrastructure=None):
        self.resources = resources or load_defaults()
        self.workflow = workflow
        self.infrastructure = infrastructure

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_workflow(
        cls,
        name: str,
        *,
        resources: dict | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Build an agent from a workflow template or YAML file."""

        if name == "default":
            workflow = default_workflow()
        else:
            path = Path(name)
            if path.exists():
                workflow = Workflow.from_yaml(str(path)).steps
            else:
                try:
                    workflow = load_template(name).steps
                except (TemplateNotFoundError, FileNotFoundError) as exc:
                    raise ValueError(f"Unknown workflow '{name}'") from exc

        return cls(
            resources=resources if resources is not None else load_defaults(),
            workflow=workflow,
            infrastructure=infrastructure,
        )

    @classmethod
    def from_workflow_dict(
        cls,
        config: dict,
        *,
        resources: dict | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Instantiate from a stage-to-plugins mapping."""

        wf = Workflow.from_dict(config)
        return cls(
            resources=resources if resources is not None else load_defaults(),
            workflow=wf.steps,
            infrastructure=infrastructure,
        )

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        *,
        resources: dict | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Create an agent from a YAML configuration file."""

        cfg = load_config(path)
        wf = Workflow.from_dict(cfg.workflow)
        return cls(
            resources=resources if resources is not None else load_defaults(),
            workflow=wf.steps,
            infrastructure=infrastructure,
        )

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
