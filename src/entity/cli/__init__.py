from __future__ import annotations

"""Simplified command line interface for running Entity agents."""

import argparse
import asyncio
import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Type

import yaml

from entity.core.agent import Agent
from entity.core.circuit_breaker import CircuitBreaker
from entity.core.plugins import Plugin
from entity.pipeline.config.config_update import update_plugin_configuration
from entity.pipeline.exceptions import CircuitBreakerTripped
from entity.utils.logging import get_logger
from entity.config.environment import load_config

logger = get_logger(__name__)


@dataclass
class CLIArgs:
    """Typed command line arguments for :class:`EntityCLI`."""

    config: Optional[str]
    state_log: Optional[str]
    command: str
    file: Optional[str] = None
    env: Optional[str] = None
    strict_stages: bool = False


class EntityCLI:
    """Expose commands for running agents and reloading configuration."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    # -----------------------------------------------------
    # argument parsing
    # -----------------------------------------------------
    def _parse_args(self) -> CLIArgs:
        parser = argparse.ArgumentParser(
            description="Run an Entity agent using a YAML configuration."
        )
        parser.add_argument("--config", "-c")
        parser.add_argument("--env")
        parser.add_argument("--state-log", dest="state_log")
        parser.add_argument("--strict-stages", action="store_true")

        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("run", help="Start the agent")
        sub.add_parser("serve-websocket", help="Start the agent via WebSocket")
        reload_p = sub.add_parser(
            "reload-config", help="Reload plugin configuration from a YAML file"
        )
        reload_p.add_argument("file")

        parsed = parser.parse_args()
        return CLIArgs(
            config=getattr(parsed, "config", None),
            state_log=getattr(parsed, "state_log", None),
            command=parsed.command,
            file=getattr(parsed, "file", None),
            env=getattr(parsed, "env", None),
            strict_stages=getattr(parsed, "strict_stages", False),
        )

    # -----------------------------------------------------
    # command dispatch
    # -----------------------------------------------------
    def run(self) -> int:  # noqa: D401 - CLI side effects
        """Execute the selected command."""
        cmd = self.args.command
        if self.args.config:
            cfg = self._load_config_files(self.args.config)
            agent = Agent.from_config(cfg, strict_stages=self.args.strict_stages)
        else:
            agent = Agent()
        if cmd == "reload-config":
            assert self.args.file is not None
            return self._reload_config(agent, self.args.file)

        async def _serve() -> None:
            await agent._ensure_runtime()
            state_logger = None
            if self.args.state_log:
                from entity.core.state_logger import StateLogger

                state_logger = StateLogger(self.args.state_log)
                agent.runtime.manager.state_logger = state_logger
            from plugins.builtin.adapters.server import AgentServer

            server = AgentServer(
                capabilities=agent.runtime.capabilities,
                manager=agent.runtime.manager,
            )
            try:
                if cmd == "serve-websocket":
                    await server.serve_websocket()
                else:
                    await server.serve_http()
            finally:
                if state_logger is not None:
                    state_logger.close()

        asyncio.run(_serve())
        return 0

    # -----------------------------------------------------
    # configuration helpers
    # -----------------------------------------------------
    def _load_config_files(
        self, config_path: str, env: str | None = None
    ) -> dict[str, Any]:
        """Load the main configuration and optional environment overlay."""
        overlay = None
        if env is None:
            env = getattr(getattr(self, "args", None), "env", None)
        if env:
            overlay = Path("config") / f"{env}.yaml"
        return load_config(config_path, overlay)

    def _validate_config(
        self,
        config_path: str,
        *,
        env: str | None = None,
        strict_stages: bool | None = None,
    ) -> int:
        async def _run() -> int:
            from entity.pipeline import SystemInitializer

            try:
                data = self._load_config_files(config_path, env)
                st = strict_stages
                if st is None:
                    st = getattr(getattr(self, "args", None), "strict_stages", False)
                initializer = SystemInitializer(data, strict_stages=st)
                await initializer.initialize()
            except Exception as exc:  # noqa: BLE001
                logger.error("Validation failed: %s", exc)
                return 1
            logger.info("Validation succeeded")
            return 0

        return asyncio.run(_run())

    def _reload_config(self, agent: Agent, file_path: str) -> int:
        """Hot-reload plugin parameters from ``file_path``."""

        if agent._runtime is None:
            if agent.config_path:
                tmp = Agent.from_config(
                    agent.config_path, strict_stages=self.args.strict_stages
                )
                agent._builder = tmp._builder
                agent._runtime = tmp._runtime

        async def _run() -> int:
            if agent._runtime is None:
                agent._runtime = await agent.builder.build_runtime()

            with open(file_path, "r", encoding="utf-8") as handle:
                new_cfg = yaml.safe_load(handle) or {}

            registry = agent.runtime.capabilities.plugins
            pipeline_manager = getattr(agent.runtime, "manager", None)

            breaker_cfg = new_cfg.get("runtime_validation_breaker", {})
            breaker = CircuitBreaker(
                failure_threshold=breaker_cfg.get("failure_threshold", 3),
                recovery_timeout=breaker_cfg.get("recovery_timeout", 60.0),
            )

            plugins = new_cfg.get("plugins", {})
            runtime_tasks = []
            for section in plugins.values():
                if not isinstance(section, dict):
                    continue
                for name, config in section.items():
                    plugin = registry.get_plugin(name)
                    if plugin is None:
                        logger.error("Plugin %s not registered", name)
                        return 2

                    config_validator = plugin.__class__.validate_config
                    if inspect.iscoroutinefunction(config_validator):
                        cfg_result = await config_validator(config)
                    else:
                        cfg_result = config_validator(config)
                    if not cfg_result.success:
                        logger.error("%s config invalid: %s", name, cfg_result.message)
                        return 1

                    dep_validator = plugin.__class__.validate_dependencies
                    if inspect.iscoroutinefunction(dep_validator):
                        dep_result = await dep_validator(registry)
                    else:
                        dep_result = dep_validator(registry)
                    if not dep_result.success:
                        logger.error(
                            "%s dependency check failed: %s",
                            name,
                            dep_result.message,
                        )
                        return 1

                    result = await update_plugin_configuration(
                        registry,
                        name,
                        config,
                        pipeline_manager=pipeline_manager,
                    )
                    if not result.success:
                        logger.error(result.error_message)
                        return 2 if result.requires_restart else 1

                    validate = getattr(plugin, "validate_runtime", None)
                    if callable(validate):

                        async def _run_validation(p: Any, plugin_name: str) -> None:
                            async def _validate() -> None:
                                v_result = await validate()
                                if not v_result.success:
                                    raise RuntimeError(v_result.message)

                            try:
                                await breaker.call(_validate)
                            except CircuitBreakerTripped as exc:
                                logger.error(
                                    "Runtime validation failure threshold exceeded: %s",
                                    exc,
                                )
                                await p.rollback_config(p.config_version - 1)
                                raise
                            except Exception as exc:  # noqa: BLE001
                                logger.error(
                                    "Runtime validation failed for %s: %s",
                                    plugin_name,
                                    exc,
                                )
                                await p.rollback_config(p.config_version - 1)
                                if breaker._failure_count >= breaker.failure_threshold:
                                    logger.error(
                                        "Runtime validation failure threshold exceeded"
                                    )
                                raise

                        runtime_tasks.append(
                            asyncio.create_task(_run_validation(plugin, name))
                        )

            for task in runtime_tasks:
                try:
                    await task
                except Exception:
                    return 1

            logger.info("Configuration updated successfully")
            return 0

        return asyncio.run(_run())


# ---------------------------------------------------------
# Helper functions from the old plugin_tool module
# ---------------------------------------------------------


def load_plugin(path: str) -> Type[Plugin]:
    mod_path = Path(path)
    module_name = mod_path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for obj in module.__dict__.values():
        if (
            inspect.isclass(obj)
            and issubclass(obj, Plugin)
            and obj is not Plugin
            and obj.__module__ == module.__name__
        ):
            return obj
    raise RuntimeError("No plugin class found")


def main() -> None:
    """Entry point used by setuptools/poetry."""
    raise SystemExit(EntityCLI().run())


__all__ = ["EntityCLI", "load_plugin", "main"]
