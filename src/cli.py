import argparse
import asyncio
import shutil
from pathlib import Path

import yaml

from common_interfaces import import_plugin_class
from common_interfaces.resources import Resource
from entity import Agent, AgentServer
from pipeline import update_plugin_configuration
from pipeline.base_plugins import ResourcePlugin, ToolPlugin
from pipeline.initializer import ClassRegistry
from pipeline.logging import get_logger

logger = get_logger(__name__)


class CLI:
    """Command line interface for the Entity agent.

    This interface can run the agent, serve over WebSocket, reload
    configuration at runtime, and scaffold new projects.
    """

    def __init__(self) -> None:
        """Initialize and parse command-line arguments."""

        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
        """Create and parse CLI arguments.

        Returns:
            argparse.Namespace: Parsed command-line arguments.
        """

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
        subparsers.add_parser("verify", help="Load plugins and exit")
        reload_parser = subparsers.add_parser(
            "reload-config",
            help="Reload plugin configuration from a YAML file",
        )
        reload_parser.add_argument("file", help="Updated configuration file")

        new_parser = subparsers.add_parser(
            "new", help="Scaffold a new project with example configuration"
        )
        new_parser.add_argument("path", help="Directory for the new project")

        return parser.parse_args()

    def run(self) -> int:
        """Execute the requested CLI action.

        Returns:
            int: Exit code of the action.
        """
        if self.args.command == "new":
            return self._create_project(self.args.path)

        if self.args.command == "verify":
            return self._verify_plugins(self.args.config)

        agent = Agent(self.args.config)
        if self.args.command == "reload-config":
            return self._reload_config(agent, self.args.file)

        async def _serve() -> None:
            await agent._ensure_runtime()
            server = AgentServer(agent.runtime)
            if self.args.command == "serve-websocket":
                await server.serve_websocket()
            else:
                await server.serve_http()

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
            """from entity import Agent\n\n\n"""
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

            async def register_new_plugin(section: str, name: str, conf: dict) -> bool:
                cls = import_plugin_class(conf.get("type", name))
                if not cls.validate_config(conf).success:
                    logger.error("Failed to validate config for %s", name)
                    return False

                class_reg = ClassRegistry()
                for n, r in getattr(resource_registry, "_resources", {}).items():
                    class_reg.register_class(r.__class__, getattr(r, "config", {}), n)
                for n, t in getattr(tool_registry, "_tools", {}).items():
                    class_reg.register_class(t.__class__, getattr(t, "config", {}), n)
                for p in plugin_registry.list_plugins():
                    class_reg.register_class(
                        p.__class__,
                        getattr(p, "config", {}),
                        plugin_registry.get_plugin_name(p),
                    )
                class_reg.register_class(cls, conf, name)

                dep_result = cls.validate_dependencies(class_reg)
                if not dep_result.success:
                    logger.error(
                        "Dependency validation failed for %s: %s",
                        name,
                        dep_result.error_message,
                    )
                    return False
                for dep in getattr(cls, "dependencies", []):
                    if not class_reg.has_plugin(dep):
                        logger.error("Missing dependency %s for plugin %s", dep, name)
                        return False

                instance = cls(conf)
                if issubclass(cls, ResourcePlugin) or issubclass(cls, Resource):
                    if hasattr(instance, "initialize") and callable(
                        instance.initialize
                    ):
                        await instance.initialize()
                    await resource_registry.add(name, instance)
                elif issubclass(cls, ToolPlugin):
                    await tool_registry.add(name, instance)
                else:
                    for stage in getattr(cls, "stages", []):
                        await plugin_registry.register_plugin_for_stage(
                            instance, stage, name
                        )
                logger.info("Registered %s", name)
                return True

            for section in ["resources", "tools", "adapters", "prompts"]:
                for name, conf in cfg.get("plugins", {}).get(section, {}).items():
                    if plugin_exists(section, name):
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
                    else:
                        ok = await register_new_plugin(section, name, conf)
                        if not ok:
                            success = False

            return 0 if success else 1

        return asyncio.run(_run())


def main() -> None:
    """Entry point for invoking the CLI."""

    raise SystemExit(CLI().run())


if __name__ == "__main__":
    main()
