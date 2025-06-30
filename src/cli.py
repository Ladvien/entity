import argparse
import asyncio
from typing import Any

import yaml

from entity import Agent
from pipeline import update_plugin_configuration
from pipeline.logging import get_logger

logger = get_logger(__name__)


class CLI:
    """Command line interface for running an Entity agent."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Run an Entity agent using a YAML configuration.",
        )
        parser.add_argument(
            "--config",
            "-c",
            required=True,
            help="Path to a YAML configuration file.",
        )

        subparsers = parser.add_subparsers(dest="command")
        parser.set_defaults(command="run")

        subparsers.add_parser("run", help="Start the agent")
        subparsers.add_parser("serve-websocket", help="Start the agent via WebSocket")
        reload_parser = subparsers.add_parser(
            "reload-config",
            help="Reload plugin configuration from a YAML file",
        )
        reload_parser.add_argument("file", help="Updated configuration file")

        return parser.parse_args()

    def run(self) -> int:
        agent = Agent(self.args.config)
        if self.args.command == "serve-websocket":
            agent.run_websocket()
            return 0
        if self.args.command == "reload-config":
            return self._reload_config(agent, self.args.file)
        agent.run_http()
        return 0

    def _reload_config(self, agent: Agent, file_path: str) -> int:
        async def _run() -> int:
            await agent._ensure_initialized()
            registries: Any | None = agent._registries
            if registries is None:
                raise RuntimeError("System not initialized")
            plugin_registry = getattr(registries, "plugins", None)
            if plugin_registry is None:
                plugin_registry = registries[0]
            with open(file_path, "r") as fh:
                cfg = yaml.safe_load(fh) or {}
            success = True
            for section in ["resources", "tools", "adapters", "prompts"]:
                for name, conf in cfg.get("plugins", {}).get(section, {}).items():
                    result = await update_plugin_configuration(
                        plugin_registry, name, conf
                    )
                    if result.success:
                        logger.info("Updated %s", name)
                    else:
                        logger.error(
                            "Failed to update %s: %s", name, result.error_message
                        )
                        success = False
            return 0 if success else 1

        return asyncio.run(_run())


def main() -> None:
    raise SystemExit(CLI().run())


if __name__ == "__main__":
    main()
