from pathlib import Path
from typing import Any, Iterable

from entity.config import load_config
from entity.defaults import load_defaults
from entity.plugins.defaults import default_workflow
from entity.workflow import WorkflowExecutor
from entity.workflow.templates import TemplateNotFoundError, load_template
from entity.workflow.workflow import Workflow


class Agent:
    """Core object composed of resources, workflow, and infrastructure."""

    _config_cache: dict[str, "Agent"] = {}

    def __init__(
        self,
        resources: dict[str, Any] | None = None,
        workflow: Workflow | None = None,
        infrastructure: object | None = None,
    ) -> None:
        if resources is None:
            resources = load_defaults()
        if not isinstance(resources, dict):
            raise TypeError("resources must be a mapping")

        self.resources = resources
        self.workflow = workflow
        self.infrastructure = infrastructure

    @classmethod
    def clear_from_config_cache(cls) -> None:
        """Reset the ``from_config`` cache."""

        cls._config_cache.clear()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_workflow(
        cls,
        name: str,
        *,
        resources: dict[str, Any] | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Build an agent from a workflow template or YAML file."""
        _resources = resources if resources is not None else load_defaults()

        if name == "default":
            workflow = default_workflow(_resources)
        else:
            path = Path(name)
            if path.exists():
                workflow = Workflow.from_yaml(str(path), _resources)
            else:
                try:
                    workflow = load_template(name, _resources)
                except (TemplateNotFoundError, FileNotFoundError) as exc:
                    raise ValueError(f"Unknown workflow '{name}'") from exc

        return cls(
            resources=_resources,
            workflow=workflow,
            infrastructure=infrastructure,
        )

    @classmethod
    def from_workflow_dict(
        cls,
        config: dict[str, Iterable[str | type]],
        *,
        resources: dict[str, Any] | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Instantiate from a stage-to-plugins mapping."""
        _resources = resources if resources is not None else load_defaults()
        wf = Workflow.from_dict(config, _resources)
        return cls(
            resources=_resources,
            workflow=wf,
            infrastructure=infrastructure,
        )

    @classmethod
    def from_config(
        cls,
        path: str | Path,
        *,
        resources: dict[str, Any] | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Create an agent from a YAML configuration file."""

        resolved = str(Path(path).resolve())
        if resources is None and infrastructure is None:
            cached = cls._config_cache.get(resolved)
            if cached is not None:
                return cached

        _resources = resources if resources is not None else load_defaults()
        cfg = load_config(resolved)
        wf = Workflow.from_dict(cfg.workflow, _resources)
        agent = cls(
            resources=_resources,
            workflow=wf,
            infrastructure=infrastructure,
        )
        if resources is None and infrastructure is None:
            cls._config_cache[resolved] = agent
        return agent

    async def chat(self, message: str, user_id: str = "default"):
        """Process ``message`` through the workflow for ``user_id``."""

        workflow = self.workflow or default_workflow(self.resources)
        executor = WorkflowExecutor(self.resources, workflow)
        result = await executor.execute(message, user_id=user_id)
        # TODO: Use a response object instead of a dict
        return {"response": result}
