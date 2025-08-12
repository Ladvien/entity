from pathlib import Path
from typing import Any, Iterable

from entity.config import load_config
from entity.defaults import load_defaults
from entity.plugins.defaults import default_workflow
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.templates import TemplateNotFoundError, load_template
from entity.workflow.workflow import Workflow


class Agent:
    """Core agent class that combines resources, workflow, and infrastructure.

    The Agent class is the main entry point for creating and running AI agents in the
    Entity framework. It follows the mental model: Agent = Resources + Workflow + Infrastructure.

    Attributes:
        resources: Dictionary of resources available to the agent (LLM, Memory, FileStorage, Logging).
        workflow: The workflow defining the agent's processing stages and plugins.
        infrastructure: Optional infrastructure configuration for deployment.

    Examples:
        Create an agent with zero configuration:

        >>> from entity import Agent
        >>> agent = Agent()  # Uses default resources and workflow
        >>> response = await agent.chat("Hello!")

        Create an agent from a workflow template:

        >>> agent = Agent.from_workflow("helpful_assistant")

        Create an agent with custom configuration:

        >>> agent = Agent.from_config("config.yaml")
    """

    _config_cache: dict[str, "Agent"] = {}

    def __init__(
        self,
        resources: dict[str, Any] | None = None,
        workflow: Workflow | None = None,
        infrastructure: object | None = None,
    ) -> None:
        """Initialize an Agent with resources, workflow, and optional infrastructure.

        Args:
            resources: Dictionary mapping resource names to resource instances.
                If None, loads default resources (vLLM, DuckDB, LocalStorage, Rich logging).
            workflow: Workflow defining the agent's processing stages.
                If None, must be set before running the agent.
            infrastructure: Optional infrastructure configuration for deployment.

        Raises:
            TypeError: If resources is not a dictionary.
        """
        if resources is None:
            resources = load_defaults()
        if not isinstance(resources, dict):
            raise TypeError("resources must be a mapping")

        self.resources = resources
        self.workflow = workflow
        self.infrastructure = infrastructure

    @classmethod
    def clear_from_config_cache(cls) -> None:
        """Clear the configuration cache for from_config method.

        This method clears the internal cache used by from_config to avoid
        recreating agents from the same configuration file. Useful when
        configuration files have been modified during runtime.
        """

        cls._config_cache.clear()

    @classmethod
    def from_workflow(
        cls,
        name: str,
        *,
        resources: dict[str, Any] | None = None,
        infrastructure: object | None = None,
    ) -> "Agent":
        """Create an agent from a workflow template or YAML file.

        Args:
            name: Either "default" for the default workflow, a path to a YAML file,
                or the name of a built-in workflow template.
            resources: Optional custom resources. If None, uses default resources.
            infrastructure: Optional infrastructure configuration.

        Returns:
            A new Agent instance configured with the specified workflow.

        Raises:
            ValueError: If the workflow name/path cannot be resolved.

        Examples:
            >>> agent = Agent.from_workflow("default")
            >>> agent = Agent.from_workflow("helpful_assistant")
            >>> agent = Agent.from_workflow("path/to/workflow.yaml")
        """
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
        """Create an agent from a dictionary mapping stages to plugins.

        Args:
            config: Dictionary mapping stage names (input, parse, think, do, review, output)
                to lists of plugin names or plugin classes.
            resources: Optional custom resources. If None, uses default resources.
            infrastructure: Optional infrastructure configuration.

        Returns:
            A new Agent instance with the specified workflow configuration.

        Examples:
            >>> agent = Agent.from_workflow_dict({
            ...     "input": ["web_input"],
            ...     "think": ["reasoning_plugin"],
            ...     "output": ["formatter_plugin"]
            ... })
        """
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
        """Create an agent from a YAML configuration file.

        This method supports caching - the same configuration file will return
        the same agent instance unless clear_from_config_cache() is called.

        Args:
            path: Path to a YAML configuration file.
            resources: Optional custom resources. If None, loads from config or defaults.
            infrastructure: Optional infrastructure. If None, loads from config.

        Returns:
            A new Agent instance configured from the YAML file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the configuration is invalid.

        Examples:
            >>> agent = Agent.from_config("config/production.yaml")
        """

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
        """Process a message through the agent's workflow.

        This is the main entry point for interacting with the agent. The message
        is processed through the 6-stage workflow (INPUT → PARSE → THINK → DO →
        REVIEW → OUTPUT) with user isolation via the user_id parameter.

        Args:
            message: The input message to process.
            user_id: Unique identifier for the user. Used to maintain separate
                conversation contexts and memory for different users. Defaults to "default".

        Returns:
            The agent's response after processing through the workflow.

        Raises:
            RuntimeError: If no workflow is configured and default workflow cannot be created.

        Examples:
            >>> agent = Agent()
            >>> response = await agent.chat("What's the weather like?")
            >>>
            >>> # Multi-user support
            >>> response1 = await agent.chat("Hello", user_id="user123")
            >>> response2 = await agent.chat("Hi", user_id="user456")
        """

        workflow = self.workflow or default_workflow(self.resources)
        executor = WorkflowExecutor(self.resources, workflow)
        result = await executor.execute(message, user_id=user_id)
        return result
