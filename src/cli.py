from __future__ import annotations

"""CLI entry point for interacting with the Entity pipeline."""

import argparse  # noqa: E402
import asyncio  # noqa: E402
import shutil  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from importlib import util
from pathlib import Path
from typing import Optional  # noqa: E402

import yaml  # noqa: E402

from entity.utils.logging import get_logger  # noqa: E402
from plugins.builtin.adapters.server import AgentServer  # noqa: E402

from entity.core.agent import Agent  # noqa: E402

logger = get_logger(__name__)


@dataclass
class CLIArgs:
    """Typed command-line arguments for :class:`CLI`."""

    config: str
    state_log: Optional[str] = None
    command: str = "run"
    path: Optional[str] = None
    file: Optional[str] = None
    workflow_cmd: Optional[str] = None
    workflow_name: Optional[str] = None
    out: Optional[str] = None
    fmt: Optional[str] = None


class CLI:
    """Command line interface for the Entity agent.

    This interface can run the agent, serve over WebSocket, reload
    configuration at runtime, and scaffold new projects.
    """

    def __init__(self) -> None:
        """Initialize and parse command-line arguments."""
        self.args: CLIArgs = self._parse_args()

    def _parse_args(self) -> CLIArgs:
        """Create and parse CLI arguments."""

        parser = argparse.ArgumentParser(
            description="Run an Entity agent using a YAML configuration.",
        )
        parser.add_argument(
            "--config",
            "-c",
            required=True,
            help="Path to a YAML configuration file.",
        )
        parser.add_argument(
            "--state-log",
            dest="state_log",
            help="Write pipeline state transitions to this file",
        )

        subparsers = parser.add_subparsers(dest="command")
        parser.set_defaults(command="run")

        subparsers.add_parser("run", help="Start the agent")
        subparsers.add_parser("serve-websocket", help="Start the agent via WebSocket")
        subparsers.add_parser("verify", help="Load plugins and exit")
        replay_parser = subparsers.add_parser(
            "replay-log", help="Replay a state log file"
        )
        replay_parser.add_argument("file", help="Log file to replay")
        reload_parser = subparsers.add_parser(
            "reload-config",
            help="Reload plugin configuration from a YAML file",
        )
        reload_parser.add_argument("file", help="Updated configuration file")

        new_parser = subparsers.add_parser(
            "new", help="Scaffold a new project with example configuration"
        )
        new_parser.add_argument("path", help="Directory for the new project")

        workflow_parser = subparsers.add_parser("workflow", help="Workflow utilities")
        wf_sub = workflow_parser.add_subparsers(dest="workflow_cmd", required=True)

        create = wf_sub.add_parser("create", help="Create a workflow module")
        create.add_argument("workflow_name", help="Workflow variable name")
        create.add_argument("--out", default="src/workflows", help="Output directory")

        validate = wf_sub.add_parser("validate", help="Validate a workflow module")
        validate.add_argument("file", help="Workflow file path")

        visualize = wf_sub.add_parser("visualize", help="Visualize workflow")
        visualize.add_argument("file", help="Workflow file path")
        visualize.add_argument(
            "--format", dest="fmt", choices=["ascii", "graphviz"], default="ascii"
        )

        args = parser.parse_args()
        return CLIArgs(
            config=args.config,
            state_log=args.state_log,
            command=args.command,
            path=getattr(args, "path", None),
            file=getattr(args, "file", None),
            workflow_cmd=getattr(args, "workflow_cmd", None),
            workflow_name=getattr(args, "workflow_name", None),
            out=getattr(args, "out", None),
            fmt=getattr(args, "fmt", None),
        )

    def run(self) -> int:
        """Execute the requested CLI action.

        Returns:
            int: Exit code of the action.
        """
        if self.args.command == "new":
            assert self.args.path is not None
            return self._create_project(self.args.path)

        if self.args.command == "verify":
            return self._verify_plugins(self.args.config)

        if self.args.command == "workflow":
            return self._handle_workflow()

        if self.args.command == "replay-log":
            from entity.core.state_logger import LogReplayer

            assert self.args.file is not None
            LogReplayer(self.args.file).replay()
            return 0

        agent = Agent(self.args.config)
        if self.args.command == "reload-config":
            assert self.args.file is not None
            return self._reload_config(agent, self.args.file)

        async def _serve() -> None:
            await agent._ensure_runtime()
            state_logger = None
            if self.args.state_log:
                from entity.core.state_logger import StateLogger

                state_logger = StateLogger(self.args.state_log)
                agent.runtime.manager.state_logger = state_logger
            server = AgentServer(agent.runtime)
            try:
                if self.args.command == "serve-websocket":
                    await server.serve_websocket()
                else:
                    await server.serve_http()
            finally:
                if state_logger is not None:
                    state_logger.close()

        asyncio.run(_serve())
        return 0

    def _create_project(self, path: str) -> int:
        """Generate a minimal project skeleton.

        Args:
            path: Destination directory for the project.

        Returns:
            int: ``0`` on success or ``1`` if the directory is not empty.
        """
        target = Path(path)
        if target.exists() and any(target.iterdir()):
            logger.error("%s already exists and is not empty", path)
            return 1

        (target / "config").mkdir(parents=True, exist_ok=True)
        (target / "src").mkdir(parents=True, exist_ok=True)

        template = Path(__file__).resolve().parent.parent / "config" / "template.yaml"
        shutil.copy(template, target / "config" / "dev.yaml")

        main_path = target / "src" / "main.py"
        main_path.write_text(
            "def main() -> None:\n"
            "    agent = Agent('config/dev.yaml')\n"
            "    agent.run_http()\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )

        logger.info("Created project at %s", target)
        return 0

    def _verify_plugins(self, config_path: str) -> int:
        """Load plugins defined in ``config_path`` and exit."""

        async def _run() -> int:
            try:
                agent = Agent(config_path)
                await agent._ensure_runtime()
            except Exception as exc:
                logger.error("Plugin loading failed: %s", exc)
                return 1
            logger.info("All plugins loaded successfully")
            return 0

        return asyncio.run(_run())

    def _reload_config(self, agent: Agent, file_path: str) -> int:
        """Reload plugin configuration placeholder."""

        logger.info(
            "Reloading configuration is not supported in this simplified build."
        )
        return 0

    # -----------------------------------------------------
    # workflow helpers
    # -----------------------------------------------------
    def _handle_workflow(self) -> int:
        cmd = self.args.workflow_cmd
        if cmd == "create":
            assert self.args.workflow_name is not None
            return self._workflow_create(self.args.workflow_name, self.args.out)
        if cmd == "validate":
            assert self.args.file is not None
            return self._workflow_validate(self.args.file)
        if cmd == "visualize":
            assert self.args.file is not None
            return self._workflow_visualize(self.args.file, self.args.fmt)
        return 0

    def _workflow_create(self, name: str, out: Optional[str]) -> int:
        assert out is not None
        out_dir = Path(out)
        out_dir.mkdir(parents=True, exist_ok=True)
        class_name = "".join(part.capitalize() for part in name.split("_"))
        template = (
            Path(__file__).resolve().parent / "templates" / "workflow_template.py"
        )
        content = template.read_text().format(workflow_name=class_name)
        dest = out_dir / f"{name}.py"
        dest.write_text(content)
        logger.info("Created %s", dest)
        return 0

    def _load_workflow(self, path: str) -> Optional[dict]:
        spec = util.spec_from_file_location(Path(path).stem, path)
        if spec is None or spec.loader is None:
            logger.error("Cannot import %s", path)
            return None
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for obj in module.__dict__.values():
            if isinstance(obj, dict):
                return obj
        logger.error("No workflow mapping found in %s", path)
        return None

    def _workflow_validate(self, path: str) -> int:
        if self._load_workflow(path) is None:
            return 1
        logger.info("Workflow validated successfully")
        return 0

    def _workflow_visualize(self, path: str, fmt: Optional[str]) -> int:
        workflow = self._load_workflow(path)
        if workflow is None:
            return 1
        if fmt == "graphviz":
            lines = ["digraph workflow {"]
            for stage, plugins in workflow.items():
                stage_name = str(stage).split(".")[-1]
                for plugin in plugins:
                    lines.append(f'    "{stage_name}" -> "{plugin}"')
            lines.append("}")
            print("\n".join(lines))
        else:
            for stage, plugins in workflow.items():
                stage_name = str(stage).split(".")[-1]
                print(stage_name)
                for plugin in plugins:
                    print(f"  -> {plugin}")
        return 0


def main() -> None:
    """Entry point for invoking the CLI."""

    raise SystemExit(CLI().run())


if __name__ == "__main__":
    main()
