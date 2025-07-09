from __future__ import annotations

"""CLI entry point for interacting with the Entity pipeline."""

import argparse  # noqa: E402
import asyncio  # noqa: E402
import shutil  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from pathlib import Path
from typing import Optional  # noqa: E402

import yaml  # noqa: E402

from pipeline import Agent  # noqa: E402
from pipeline import update_plugin_configuration  # noqa: E402
from pipeline.logging import get_logger  # noqa: E402
from plugins.builtin.adapters.server import AgentServer  # noqa: E402

logger = get_logger(__name__)


@dataclass
class CLIArgs:
    """Typed command-line arguments for :class:`CLI`."""

    config: str
    state_log: Optional[str] = None
    command: str = "run"
    path: Optional[str] = None
    file: Optional[str] = None


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

        args = parser.parse_args()
        return CLIArgs(
            config=args.config,
            state_log=args.state_log,
            command=args.command,
            path=getattr(args, "path", None),
            file=getattr(args, "file", None),
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

        if self.args.command == "replay-log":
            from pipeline.state_logger import LogReplayer

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
                from pipeline.state_logger import StateLogger

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
        """Reload plugin configuration for a running agent.

        Args:
            agent: Target agent instance.
            file_path: YAML file containing updated plugin configuration.

        Returns:
            int: ``0`` when successful, ``1`` otherwise.
        """

        async def _run() -> int:
            await agent._ensure_runtime()

            registries = agent.runtime.registries

            resource_registry = getattr(registries, "resources", registries[1])
            tool_registry = getattr(registries, "tools", registries[2])
            plugin_registry = getattr(registries, "plugins", registries[0])

            with open(file_path, "r") as fh:
                cfg = yaml.safe_load(fh) or {}

            success = True

            def plugin_exists(section: str, plugin_name: str) -> bool:
                if section == "resources":
                    return plugin_name in getattr(resource_registry, "_resources", {})
                if section == "tools":
                    return plugin_name in getattr(tool_registry, "_tools", {})
                for p in plugin_registry.list_plugins():
                    if plugin_registry.get_plugin_name(p) == plugin_name:
                        return True
                return False

            for section in ["resources", "tools", "adapters", "prompts"]:
                for name, conf in cfg.get("plugins", {}).get(section, {}).items():
                    if not plugin_exists(section, name):
                        logger.error(
                            "Plugin %s not found. Restart required to add new plugins",
                            name,
                        )
                        success = False
                        continue

                    result = await update_plugin_configuration(
                        plugin_registry, name, conf
                    )
                    if result.success:
                        logger.info("Updated %s", name)
                    elif result.requires_restart:
                        logger.error("%s", result.error_message)
                        success = False
                    else:
                        logger.error(
                            "Failed to update %s: %s", name, result.error_message
                        )
                        success = False

            return 0 if success else 1

        return asyncio.run(_run())


def main() -> None:
    """Entry point for invoking the CLI."""

    raise SystemExit(CLI().run())


if __name__ == "__main__":
    main()
