from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from entity.core.agent import Agent
from entity.plugins.defaults import default_workflow
from entity.cli.ent_cli_adapter import EntCLIAdapter
from entity.resources.logging import LoggingResource
from entity.defaults import load_defaults
from entity.workflow.templates.loader import load_template, TemplateNotFoundError
from entity.workflow.workflow import Workflow
from entity.workflow.executor import WorkflowExecutor
from entity.plugins.context import PluginContext


def _load_workflow(name: str) -> list[type] | dict[str, list[type]]:
    """Return workflow steps from ``name`` or exit with a helpful error."""

    if name == "default":
        steps = list(default_workflow())
        if steps and steps[0] is EntCLIAdapter:
            steps = steps[1:]
        if steps and steps[-1] is EntCLIAdapter:
            steps = steps[:-1]
        return steps

    path = Path(name)
    if path.exists():
        try:
            return Workflow.from_yaml(str(path)).steps
        except Exception as exc:  # pragma: no cover - corrupt file
            raise SystemExit(f"Failed to load workflow file '{name}': {exc}") from exc

    try:
        return load_template(name).steps
    except TemplateNotFoundError as exc:
        raise SystemExit(f"Workflow template '{name}' not found") from exc


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
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Maximum seconds to wait for the workflow to complete",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> None:
    level = "debug" if args.verbose else "error" if args.quiet else "info"
    resources = load_defaults()
    resources["logging"] = LoggingResource(level)
    workflow = _load_workflow(args.workflow)
    agent = Agent(resources=resources, workflow=workflow)

    adapter = EntCLIAdapter(resources)
    try:
        in_ctx = PluginContext(resources, "cli")
        in_ctx.current_stage = WorkflowExecutor.INPUT
        message = await adapter.execute(in_ctx)
        if not message:
            return

        if args.timeout:
            result = await asyncio.wait_for(agent.chat(message), args.timeout)
        else:
            result = await agent.chat(message)

        out_ctx = PluginContext(resources, "cli")
        out_ctx.current_stage = WorkflowExecutor.OUTPUT
        out_ctx.message = result["response"]
        out_ctx.say(result["response"])
        await adapter.execute(out_ctx)
    except KeyboardInterrupt:  # pragma: no cover - user interrupt
        pass
    except asyncio.TimeoutError:
        print("Execution timed out", file=sys.stderr)
        adapter.stop()
        return
    finally:
        await adapter.wait_closed()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
