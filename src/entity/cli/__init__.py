from __future__ import annotations

"""Unified command line interface for the Entity framework."""

import argparse
import asyncio
import importlib.util
import inspect
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Type

import yaml

from entity.core.agent import Agent
from entity.core.plugins import BasePlugin, ValidationResult
from entity.utils.logging import get_logger
from cli.plugin_tool.generate import generate_plugin
from cli.plugin_tool.utils import load_plugin
from cli.plugin_tool.main import PLUGIN_TYPES

logger = get_logger(__name__)


@dataclass
class CLIArgs:
    """Typed command line arguments for :class:`EntityCLI`."""

    config: Optional[str]
    state_log: Optional[str]
    command: str
    plugin_cmd: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    out: Optional[str] = None
    docs_dir: Optional[str] = None
    path: Optional[str] = None
    paths: Optional[list[str]] = None
    file: Optional[str] = None
    workflow_cmd: Optional[str] = None
    workflow_name: Optional[str] = None
    fmt: Optional[str] = None


class EntityCLI:
    """Expose commands for running agents and working with plugins."""

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
        parser.add_argument("--state-log", dest="state_log")

        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("run", help="Start the agent")
        sub.add_parser("serve-websocket", help="Start the agent via WebSocket")
        sub.add_parser("verify", help="Load plugins and exit")
        search = sub.add_parser("search-plugin", help="Search the plugin marketplace")
        search.add_argument("name")
        replay = sub.add_parser("replay-log", help="Replay a state log file")
        replay.add_argument("file")
        reload_p = sub.add_parser(
            "reload-config", help="Reload plugin configuration from a YAML file"
        )
        reload_p.add_argument("file")

        new_p = sub.add_parser("new", help="Scaffold a new project")
        new_p.add_argument("path")

        create_agent = sub.add_parser("create-agent", help="Create a new agent project")
        create_agent.add_argument("name")

        workflow = sub.add_parser("workflow", help="Workflow utilities")
        wf_sub = workflow.add_subparsers(dest="workflow_cmd", required=True)
        create = wf_sub.add_parser("create", help="Create a workflow module")
        create.add_argument("workflow_name")
        create.add_argument("--out", default="src/workflows")
        validate = wf_sub.add_parser("validate", help="Validate a workflow module")
        validate.add_argument("file")
        visualize = wf_sub.add_parser("visualize", help="Visualize workflow")
        visualize.add_argument("file")
        visualize.add_argument(
            "--format", dest="fmt", choices=["ascii", "graphviz"], default="ascii"
        )

        plugin = sub.add_parser("plugin", help="Plugin development tools")
        plug_sub = plugin.add_subparsers(dest="plugin_cmd", required=True)
        gen = plug_sub.add_parser("generate", help="Generate plugin boilerplate")
        gen.add_argument("name")
        gen.add_argument("--type", required=True, choices=list(PLUGIN_TYPES))
        gen.add_argument("--out", default="src")
        gen.add_argument("--docs-dir", default="docs/source")

        val = plug_sub.add_parser("validate", help="Validate plugin structure")
        val.add_argument("path")

        tst = plug_sub.add_parser("test", help="Run plugin in isolation")
        tst.add_argument("path")

        cfg = plug_sub.add_parser("config", help="Interactive configuration builder")
        cfg.add_argument("--name", required=True)
        cfg.add_argument("--type", required=True, choices=list(PLUGIN_TYPES))

        dep = plug_sub.add_parser("deps", help="Analyze plugin dependencies")
        dep.add_argument("paths", nargs="+")

        doc = plug_sub.add_parser("docs", help="Generate documentation for plugin")
        doc.add_argument("path")
        doc.add_argument("--out", default="docs/source")

        ana = plug_sub.add_parser(
            "analyze-plugin", help="Suggest pipeline stages for plugin functions"
        )
        ana.add_argument("path")

        parsed = parser.parse_args()
        return CLIArgs(
            config=getattr(parsed, "config", None),
            state_log=getattr(parsed, "state_log", None),
            command=parsed.command,
            plugin_cmd=getattr(parsed, "plugin_cmd", None),
            name=getattr(parsed, "name", None),
            type=getattr(parsed, "type", None),
            out=getattr(parsed, "out", None),
            docs_dir=getattr(parsed, "docs_dir", None),
            path=getattr(parsed, "path", None),
            paths=getattr(parsed, "paths", None),
            file=getattr(parsed, "file", None),
            workflow_cmd=getattr(parsed, "workflow_cmd", None),
            workflow_name=getattr(parsed, "workflow_name", None),
            fmt=getattr(parsed, "fmt", None),
        )

    # -----------------------------------------------------
    # command dispatch
    # -----------------------------------------------------
    def run(self) -> int:  # noqa: D401 - CLI side effects
        """Execute the selected command."""
        cmd = self.args.command
        if cmd == "plugin":
            return self._handle_plugin()
        if cmd == "create-agent":
            assert self.args.name is not None
            return self._create_agent(self.args.name)
        if cmd == "new":
            assert self.args.path is not None
            return self._create_project(self.args.path)
        if cmd == "verify":
            assert self.args.config is not None
            return self._verify_plugins(self.args.config)
        if cmd == "search-plugin":
            assert self.args.name is not None
            return self._search_plugin(self.args.name)
        if cmd == "workflow":
            return self._handle_workflow()
        if cmd == "replay-log":
            assert self.args.file is not None
            from entity.core.state_logger import LogReplayer

            LogReplayer(self.args.file).replay()
            return 0
        agent = Agent(self.args.config) if self.args.config else Agent()
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

            server = AgentServer(agent.runtime)
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
    # plugin helpers
    # -----------------------------------------------------
    def _handle_plugin(self) -> int:
        pcmd = self.args.plugin_cmd
        if pcmd == "generate":
            assert self.args.name and self.args.type
            out = Path(self.args.out or "src")
            docs = Path(self.args.docs_dir or "docs/source")
            return generate_plugin(self.args.name, self.args.type, out, docs)
        if pcmd == "validate":
            assert self.args.path
            return self._plugin_validate(self.args.path)
        if pcmd == "test":
            assert self.args.path
            return self._plugin_test(self.args.path)
        if pcmd == "config":
            assert self.args.name and self.args.type
            return self._plugin_config(self.args.name, self.args.type)
        if pcmd == "deps":
            assert self.args.paths
            return self._plugin_deps(self.args.paths)
        if pcmd == "docs":
            assert self.args.path
            out = Path(self.args.out or "docs/source")
            return self._plugin_docs(self.args.path, out)
        if pcmd == "analyze-plugin":
            assert self.args.path
            return self._analyze_plugin(self.args.path)
        return 0

    def _plugin_validate(self, path: str) -> int:
        plugin_cls = load_plugin(path)
        if not issubclass(plugin_cls, BasePlugin):
            logger.error("Not a plugin class")
            return 1
        if not getattr(plugin_cls, "stages", None):
            logger.error("Plugin does not define stages")
            return 1
        result = plugin_cls.validate_config(getattr(plugin_cls, "config", {}))
        if not isinstance(result, ValidationResult) or not result.success:
            logger.error("Config validation failed: %s", result.error_message)
            return 1
        logger.info("Validation succeeded")
        return 0

    def _plugin_test(self, path: str) -> int:
        plugin_cls = load_plugin(path)
        instance = plugin_cls(getattr(plugin_cls, "config", {}))
        if hasattr(instance, "initialize") and callable(instance.initialize):
            logger.info("Initializing plugin...")
            asyncio.run(instance.initialize())
        if hasattr(instance, "_execute_impl"):
            logger.info("Executing plugin...")

            class DummyContext:
                async def __getattr__(self, _: str) -> Callable[..., Awaitable[None]]:
                    async def _noop(*_a: Any, **_kw: Any) -> None:
                        return None

                    return _noop

            ctx = DummyContext()
            try:
                if inspect.iscoroutinefunction(instance._execute_impl):
                    asyncio.run(instance._execute_impl(ctx))
                else:
                    instance._execute_impl(ctx)
            except Exception as exc:  # pragma: no cover - manual testing
                logger.error("Execution failed: %s", exc)
                return 1
        logger.info("Plugin executed successfully")
        return 0

    def _plugin_config(self, name: str, ptype: str) -> int:
        cfg: dict[str, str] = {}
        logger.info("Building configuration for %s (%s)", name, ptype)
        while True:
            key = input("key (blank to finish): ").strip()
            if not key:
                break
            value = input(f"value for '{key}': ").strip()
            cfg[key] = value
        section = self._section_for_type(ptype)
        output = yaml.dump({"plugins": {section: {name: cfg}}})
        logger.info("\n%s", output)
        return 0

    def _plugin_deps(self, paths: list[str]) -> int:
        for p in paths:
            cls = load_plugin(p)
            deps = getattr(cls, "dependencies", [])
            name = cls.__name__
            logger.info("%s: %s", name, ", ".join(deps) if deps else "no dependencies")
        return 0

    def _plugin_docs(self, path: str, out_dir: Path) -> int:
        cls = load_plugin(path)
        out_dir.mkdir(parents=True, exist_ok=True)
        name = cls.__name__.lower()
        doc_path = out_dir / f"{name}.md"
        doc = inspect.getdoc(cls) or cls.__name__
        doc_path.write_text(f"# {cls.__name__}\n\n{doc}\n")
        logger.info("Documentation written to %s", doc_path)
        return 0

    def _analyze_plugin(self, path: str) -> int:
        spec = importlib.util.spec_from_file_location(Path(path).stem, path)
        if spec is None or spec.loader is None:
            logger.error("Cannot import %s", path)
            return 1
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from entity.core.plugin_utils import PluginAutoClassifier

        found = False
        for name, obj in module.__dict__.items():
            if name.startswith("_"):
                continue
            if inspect.iscoroutinefunction(obj):
                plugin = PluginAutoClassifier.classify(obj)
                stages = ", ".join(str(s) for s in plugin.stages)
                logger.info("%s -> %s", name, stages)
                found = True
        if not found:
            logger.error("No async plugin functions found in %s", path)
            return 1
        return 0

    def _search_plugin(self, name: str) -> int:
        """Placeholder for future plugin marketplace search."""
        logger.info("search-plugin '%s' is not implemented yet", name)
        return 0

    @staticmethod
    def _section_for_type(ptype: str) -> str:
        if ptype == "resource":
            return "resources"
        if ptype == "tool":
            return "tools"
        if ptype == "adapter":
            return "adapters"
        if ptype == "prompt":
            return "prompts"
        return "failures"

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
        spec = importlib.util.spec_from_file_location(Path(path).stem, path)
        if spec is None or spec.loader is None:
            logger.error("Cannot import %s", path)
            return None
        module = importlib.util.module_from_spec(spec)
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

    # -----------------------------------------------------
    # configuration helpers
    # -----------------------------------------------------
    async def _verify_plugins(self, config_path: str) -> int:
        async def _run() -> int:
            try:
                agent = Agent(config_path)
                await agent._ensure_runtime()
            except Exception as exc:  # noqa: BLE001
                logger.error("Plugin loading failed: %s", exc)
                return 1
            logger.info("All plugins loaded successfully")
            return 0

        return asyncio.run(_run())

    def _reload_config(self, agent: Agent, file_path: str) -> int:
        logger.info(
            "Reloading configuration is not supported in this simplified build."
        )
        return 0

    def _create_project(self, path: str) -> int:
        target = Path(path)
        if target.exists() and any(target.iterdir()):
            logger.error("%s already exists and is not empty", path)
            return 1
        (target / "config").mkdir(parents=True, exist_ok=True)
        (target / "src").mkdir(parents=True, exist_ok=True)
        template = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "config"
            / "template.yaml"
        )
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

    def _create_agent(self, name: str) -> int:
        """Scaffold a simple agent project."""
        target = Path(name)
        if target.exists() and any(target.iterdir()):
            logger.error("%s already exists and is not empty", name)
            return 1

        (target / "config").mkdir(parents=True, exist_ok=True)
        (target / "src").mkdir(parents=True, exist_ok=True)

        template = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "config"
            / "template.yaml"
        )
        shutil.copy(template, target / "config" / "dev.yaml")

        main_path = target / "src" / "main.py"
        main_code = (
            "from entity.core.agent import Agent\n\n"
            "def main() -> None:\n"
            "    agent = Agent('config/dev.yaml')\n"
            "    agent.run_http()\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        main_path.write_text(main_code)

        logger.info("Created agent project at %s", target)
        return 0


def main() -> None:
    """Entry point used by setuptools/poetry."""
    raise SystemExit(EntityCLI().run())


__all__ = ["EntityCLI", "main"]
