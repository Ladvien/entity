from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from entity.core.agent import Agent
from entity.plugins.defaults import default_workflow
from entity.cli.ent_cli_adapter import EntCLIAdapter
from entity.resources.logging import LoggingResource
from entity.defaults import load_defaults
from entity.workflow.templates.loader import load_template, TemplateNotFoundError
from entity.workflow.workflow import Workflow
from entity.workflow.executor import WorkflowExecutor


def _load_workflow(name: str) -> list[type] | dict[str, list[type]]:
    if name == "default":
        return default_workflow()

    path = Path(name)
    try:
        if path.exists():
            wf = Workflow.from_yaml(str(path))
        else:
            wf = load_template(name)
    except (TemplateNotFoundError, FileNotFoundError):
        raise SystemExit(f"Unknown workflow '{name}'")

    steps = wf.steps
    steps.setdefault(WorkflowExecutor.INPUT, []).insert(0, EntCLIAdapter)
    steps.setdefault(WorkflowExecutor.OUTPUT, []).append(EntCLIAdapter)
    return steps


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an Entity workflow")
    parser.add_argument(
        "--workflow",
        default="default",
        help="Workflow template name or YAML path",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress informational logs",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    level = "debug" if args.verbose else "error" if args.quiet else "info"
    resources = load_defaults()
    resources["logging"] = LoggingResource(level)
    workflow = _load_workflow(args.workflow)
    agent = Agent(resources=resources, workflow=workflow)
    try:
        await agent.chat("")
    except KeyboardInterrupt:  # pragma: no cover - user interrupt
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
