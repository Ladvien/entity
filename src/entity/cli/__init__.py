from __future__ import annotations

"""Minimal command line interface for the Entity framework."""

import argparse
import asyncio
from pathlib import Path
from typing import Any

import yaml

from entity.core.agent import Agent
from plugins.builtin.adapters.server import AgentServer


class EntityCLI:
    """Expose simple commands for interacting with an agent."""

    def __init__(self) -> None:
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Entity command line")
        sub = parser.add_subparsers(dest="command", required=True)

        run_p = sub.add_parser("run", help="Start an HTTP server from config")
        run_p.add_argument("--config", "-c", required=True)

        list_p = sub.add_parser("list-plugins", help="List configured plugins")
        list_p.add_argument("--config", "-c", required=True)

        val_p = sub.add_parser("validate", help="Validate configuration")
        val_p.add_argument("--config", "-c", required=True)
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parser.parse_args(argv)
        cmd = args.command
        if cmd == "run":
            return asyncio.run(self._run_agent(args.config))
        if cmd == "list-plugins":
            return asyncio.run(self._list_plugins(args.config))
        if cmd == "validate":
            return asyncio.run(self._validate(args.config))
        self.parser.print_help()
        return 0

    async def _load_agent(self, config_path: str) -> Agent:
        agent = Agent(config_path)
        await agent._ensure_runtime()
        return agent

    async def _run_agent(self, config_path: str) -> int:
        agent = await self._load_agent(config_path)
        cfg = _load_yaml(config_path)
        server_cfg = cfg.get("server", {}) if isinstance(cfg, dict) else {}
        host = server_cfg.get("host", "127.0.0.1")
        port = int(server_cfg.get("port", 8000))
        server = AgentServer(agent.runtime)
        await server.serve_http(host=host, port=port)
        return 0

    async def _list_plugins(self, config_path: str) -> int:
        agent = await self._load_agent(config_path)
        registry = agent.get_registries().plugins
        for plugin in registry.list_plugins():
            print(registry.get_plugin_name(plugin))
        return 0

    async def _validate(self, config_path: str) -> int:
        try:
            await self._load_agent(config_path)
        except Exception as exc:  # noqa: BLE001
            print(f"Configuration invalid: {exc}")
            return 1
        print("Configuration valid")
        return 0


def _load_yaml(path: str) -> Any:
    with open(Path(path), "r") as fh:
        return yaml.safe_load(fh) or {}


def main() -> None:
    """Console entry point."""

    raise SystemExit(EntityCLI().run())


__all__ = ["EntityCLI", "main"]
