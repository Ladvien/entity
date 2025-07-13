from __future__ import annotations

"""Unified command line interface for the Entity framework."""

import argparse
import asyncio
import importlib.util
import inspect
import shutil
import difflib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

import yaml
from jsonschema import Draft7Validator

from entity.core.agent import Agent
from entity.core.plugins import Plugin, ValidationResult
from entity.pipeline.config.config_update import update_plugin_configuration
from entity.pipeline.exceptions import CircuitBreakerTripped
from entity.core.circuit_breaker import CircuitBreaker
from entity.utils.logging import get_logger
from entity.config.environment import load_config
from docs.generate_config_docs import build_schema
from importlib import import_module  # noqa: E402
from entity.infrastructure import (
    DockerInfrastructure,
    AWSStandardInfrastructure,
)  # noqa: E402

try:  # Resolve plugin helpers from installed "cli" package
    generate_plugin = import_module("cli.plugin_tool.generate").generate_plugin
    load_plugin = import_module("cli.plugin_tool.utils").load_plugin
    PLUGIN_TYPES = import_module("cli.plugin_tool.main").PLUGIN_TYPES
except ModuleNotFoundError:  # Fallback for local executions without package mode
    cli_path = Path(__file__).resolve().parents[2] / "cli"
    if str(cli_path) not in sys.path:
        sys.path.insert(0, str(cli_path))
    generate_plugin = import_module("plugin_tool.generate").generate_plugin
    load_plugin = import_module("plugin_tool.utils").load_plugin
    PLUGIN_TYPES = import_module("plugin_tool.main").PLUGIN_TYPES

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
    env: Optional[str] = None
    infra_cmd: Optional[str] = None
    infra_type: Optional[str] = None
    infra_path: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None
    files: Optional[list[str]] = None


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
        parser.add_argument("--env")
        parser.add_argument("--state-log", dest="state_log")
        parser.add_argument("--strict-stages", action="store_true")

        sub = parser.add_subparsers(dest="command", required=True)
        sub.add_parser("run", help="Start the agent")
        sub.add_parser("serve-websocket", help="Start the agent via WebSocket")
        sub.add_parser("verify", help="Load plugins and exit")
        sub.add_parser("validate", help="Validate configuration and exit")
        search = sub.add_parser("search-plugin", help="Search the plugin marketplace")
        search.add_argument("name")
        replay = sub.add_parser("replay-log", help="Replay a state log file")
        replay.add_argument("file")
        reload_p = sub.add_parser(
            "reload-config", help="Reload plugin configuration from a YAML file"
        )
        reload_p.add_argument("file")

        diff_p = sub.add_parser(
            "diff-config", help="Show differences with the current configuration"
        )
        diff_p.add_argument("file")

        lint_p = sub.add_parser(
            "lint-config", help="Validate configuration files against schema"
        )
        lint_p.add_argument("files", nargs="+")

        stats = sub.add_parser(
            "get-conversation-stats", help="Show conversation metrics"
        )
        stats.add_argument("user_id")

        debug = sub.add_parser("debug", help="Step through pipeline execution")
        debug.add_argument("message", help="Input message")

        new_p = sub.add_parser("new", help="Scaffold a new project")
        new_p.add_argument("path")

        create_agent = sub.add_parser("create-agent", help="Create a new agent project")
        create_agent.add_argument("name")

        workflow = sub.add_parser("workflow", help="Workflow utilities")
        wf_sub = workflow.add_subparsers(dest="workflow_cmd", required=True)
        create = wf_sub.add_parser("create", help="Create a workflow module")
        create.add_argument("workflow_name")
        create.add_argument("--out", default="src/workflows")
        validate = wf_sub.add_parser(
            "validate", help="Validate a workflow module or YAML file"
        )
        validate.add_argument("file", help="Workflow .py or .yaml file")
        visualize = wf_sub.add_parser(
            "visualize",
            help="Visualize workflow from module or YAML file",
        )
        visualize.add_argument("file", help="Workflow .py or .yaml file")
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

        scaffold = plug_sub.add_parser(
            "scaffold", help="Create a standalone plugin project"
        )
        scaffold.add_argument("name")
        scaffold.add_argument("--type", required=True, choices=list(PLUGIN_TYPES))
        scaffold.add_argument("--out", default="user_plugins")

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
            "analyze-plugin",
            help=(
                "Show plugin stages and whether they come from config hints"
                " or class attributes"
            ),
        )
        ana.add_argument("path")

        infra = sub.add_parser("infra", help="Infrastructure operations")
        infra_sub = infra.add_subparsers(dest="infra_cmd", required=True)
        deploy = infra_sub.add_parser("deploy", help="Deploy infrastructure")
        deploy.add_argument("--type", required=True, dest="infra_type")
        deploy.add_argument("--path", dest="infra_path", default="infra")
        destroy = infra_sub.add_parser("destroy", help="Destroy infrastructure")
        destroy.add_argument("--type", required=True, dest="infra_type")
        destroy.add_argument("--path", dest="infra_path", default="infra")

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
            env=getattr(parsed, "env", None),
            infra_cmd=getattr(parsed, "infra_cmd", None),
            infra_type=getattr(parsed, "infra_type", None),
            infra_path=getattr(parsed, "infra_path", None),
            user_id=getattr(parsed, "user_id", None),
            message=getattr(parsed, "message", None),
            files=getattr(parsed, "files", None),
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
        if cmd == "validate":
            assert self.args.config is not None
            return self._validate_config(self.args.config)
        if cmd == "search-plugin":
            assert self.args.name is not None
            return self._search_plugin(self.args.name)
        if cmd == "workflow":
            return self._handle_workflow()
        if cmd == "infra":
            return self._handle_infra()
        if cmd == "replay-log":
            assert self.args.file is not None
            from entity.core.state_logger import LogReplayer

            LogReplayer(self.args.file).replay()
            return 0
        if self.args.config:
            cfg = self._load_config_files(self.args.config)
            agent = Agent.from_config(cfg, strict_stages=self.args.strict_stages)
        else:
            agent = Agent()
        if cmd == "debug":
            assert self.args.message is not None
            return asyncio.run(self._debug_run(agent, self.args.message))
        if cmd == "get-conversation-stats":
            assert self.args.user_id is not None
            return asyncio.run(self._get_conversation_stats(agent, self.args.user_id))
        if cmd == "reload-config":
            assert self.args.file is not None
            return self._reload_config(agent, self.args.file)
        if cmd == "diff-config":
            assert self.args.file is not None
            return self._diff_config(agent, self.args.file)
        if cmd == "lint-config":
            assert self.args.files is not None
            return self._lint_config(self.args.files)

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
        if pcmd == "scaffold":
            assert self.args.name and self.args.type
            out = Path(self.args.out or "user_plugins")
            return self._plugin_scaffold(self.args.name, self.args.type, out)
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
        if not issubclass(plugin_cls, Plugin):
            logger.error("Not a plugin class")
            return 1
        if not getattr(plugin_cls, "stages", None):
            logger.error("Plugin does not define stages")
            return 1
        result = asyncio.run(
            plugin_cls.validate_config(getattr(plugin_cls, "config", {}))
        )
        if not isinstance(result, ValidationResult) or not result.success:
            logger.error("Config validation failed: %s", result.error_message)
            return 1

        class _DummyRegistry:
            def has_plugin(self, _name: str) -> bool:  # noqa: D401 - simple impl
                return False

            def list_plugins(self) -> list[str]:
                return []

        dep_result = asyncio.run(plugin_cls.validate_dependencies(_DummyRegistry()))
        if not isinstance(dep_result, ValidationResult) or not dep_result.success:
            logger.error("Dependency validation failed: %s", dep_result.error_message)
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

    def _plugin_scaffold(self, name: str, ptype: str, dest: Path) -> int:
        if dest.exists() and any(dest.iterdir()):
            logger.error("%s already exists and is not empty", dest)
            return 1
        src_dir = dest / "src"
        docs_dir = dest / "docs"
        tests_dir = dest / "tests"
        src_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        template = Path("templates/plugins") / f"{ptype}.py"
        class_name = "".join(part.capitalize() for part in name.split("_"))
        content = template.read_text().format(class_name=class_name)
        (src_dir / f"{name}.py").write_text(content)
        (docs_dir / f"{name}.md").write_text(
            f"## {class_name}\n\n.. automodule:: {name}\n    :members:\n"
        )
        test_path = tests_dir / f"test_{name}.py"
        test_code = (
            "from pathlib import Path\n"
            "from tests.plugins.harness import run_plugin\n\n"
            f"def test_{name}():\n"
            "    path = Path(__file__).parents[1] / 'src' / '{name}.py'\n"
            "    run_plugin(str(path))\n"
        )
        test_path.write_text(test_code)
        logger.info("Created plugin project at %s", dest)
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
                if getattr(plugin, "_explicit_stages", False):
                    reason = "config hints"
                else:
                    reason = "class attributes"
                logger.info("%s -> %s (%s)", name, stages, reason)
                found = True
        if not found:
            logger.error("No async plugin functions found in %s", path)
            return 1
        return 0

    def _search_plugin(self, name: str) -> int:
        """Placeholder for future plugin marketplace search."""
        logger.info("search-plugin '%s' is not implemented yet", name)
        return 0

    # -----------------------------------------------------
    # infrastructure helpers
    # -----------------------------------------------------
    def _handle_infra(self) -> int:
        cmd = self.args.infra_cmd
        typ = self.args.infra_type or ""
        path = self.args.infra_path or "infra"
        if cmd == "deploy":
            return asyncio.run(self._infra_deploy(typ, path))
        if cmd == "destroy":
            return asyncio.run(self._infra_destroy(typ, path))
        return 0

    async def _infra_deploy(self, typ: str, path: str) -> int:
        if typ == "docker":
            infra = DockerInfrastructure({"path": path})
        elif typ == "aws-standard":
            infra = AWSStandardInfrastructure(region="us-east-1", config={"path": path})
        else:
            logger.error("Unknown infrastructure type %s", typ)
            return 1
        await infra.deploy()
        return 0

    async def _infra_destroy(self, typ: str, path: str) -> int:
        if typ == "docker":
            infra = DockerInfrastructure({"path": path})
        elif typ == "aws-standard":
            infra = AWSStandardInfrastructure(region="us-east-1", config={"path": path})
        else:
            logger.error("Unknown infrastructure type %s", typ)
            return 1
        await infra.destroy()
        return 0

    async def _get_conversation_stats(self, agent: Agent, user_id: str) -> int:
        await agent._ensure_runtime()
        memory = agent.runtime.capabilities.resources.get("memory")
        if memory is None:
            logger.error("Memory resource not configured")
            return 1
        stats = await memory.conversation_statistics(user_id)
        print(yaml.safe_dump(stats))
        return 0

    async def _debug_run(self, agent: Agent, message: str) -> int:
        await agent._ensure_runtime()
        from entity.debug import PipelineDebugger

        debugger = PipelineDebugger(agent.runtime.capabilities)
        response, tracer = await debugger.run(
            message, user_id=self.args.user_id or "debug"
        )
        print(yaml.safe_dump(response))
        print(yaml.safe_dump(tracer.report()))
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
        p = Path(path)
        if p.suffix.lower() in {".yaml", ".yml"}:
            try:
                data = yaml.safe_load(p.read_text()) or {}
            except Exception as exc:  # noqa: BLE001
                logger.error("Cannot parse %s: %s", path, exc)
                return None

            workflow = data.get("workflow")
            if isinstance(workflow, dict):
                return workflow

            logger.error("No workflow mapping found in %s", path)
            return None

        spec = importlib.util.spec_from_file_location(p.stem, path)
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
    def _load_config_files(self, config_path: str) -> dict[str, Any]:
        overlay = None
        if self.args.env:
            overlay = Path("config") / f"{self.args.env}.yaml"
        return load_config(config_path, overlay)

    async def _verify_plugins(self, config_path: str) -> int:
        async def _run() -> int:
            from entity.pipeline import SystemInitializer
            import yaml
            from pathlib import Path

            try:
                data = yaml.safe_load(Path(config_path).read_text()) or {}
                initializer = SystemInitializer(
                    data, strict_stages=self.args.strict_stages
                )
                await initializer.initialize()
            except Exception as exc:  # noqa: BLE001
                logger.error("Plugin validation failed: %s", exc)
                return 1
            logger.info("All plugins loaded successfully")
            return 0

        return asyncio.run(_run())

    def _validate_config(self, config_path: str) -> int:
        async def _run() -> int:
            from entity.pipeline import SystemInitializer

            try:
                data = self._load_config_files(config_path)
                initializer = SystemInitializer(
                    data, strict_stages=self.args.strict_stages
                )
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

    def _diff_config(self, agent: Agent, file_path: str) -> int:
        """Show differences between running config and ``file_path``."""

        if agent.config_path is None:
            logger.error("Agent was not started from a config file")
            return 1

        current = self._load_config_files(agent.config_path)
        with open(file_path, "r", encoding="utf-8") as handle:
            new_cfg = yaml.safe_load(handle) or {}

        diff = difflib.unified_diff(
            yaml.safe_dump(current, sort_keys=True).splitlines(),
            yaml.safe_dump(new_cfg, sort_keys=True).splitlines(),
            fromfile="current",
            tofile=file_path,
        )
        print("\n".join(diff))
        return 0

    def _lint_config(self, files: list[str]) -> int:
        """Validate YAML files against the generated configuration schema."""

        schema = build_schema()["EntityConfig"]
        validator = Draft7Validator(schema)
        ok = True
        for path in files:
            data = yaml.safe_load(Path(path).read_text()) or {}
            errors = list(validator.iter_errors(data))
            if errors:
                ok = False
                logger.error("%s is invalid", path)
                for err in errors:
                    logger.error("  %s", err.message)
        return 0 if ok else 1

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
