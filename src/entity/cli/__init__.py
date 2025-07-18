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
<<<<<<< HEAD
from entity.utils.logging import get_logger
from entity.config.environment import load_config
from importlib import import_module  # noqa: E402
from entity.infrastructure import (
    DockerInfrastructure,
)  # noqa: E402

try:  # Resolve plugin helpers from installed package
    generate_plugin = import_module("entity.cli.plugin_tool.generate").generate_plugin
    load_plugin = import_module("entity.cli.plugin_tool.utils").load_plugin
    PLUGIN_TYPES = import_module("entity.cli.plugin_tool.main").PLUGIN_TYPES
except ModuleNotFoundError:  # Fallback for local executions without package mode
    cli_path = Path(__file__).resolve().parents[2] / "cli"
    if str(cli_path) not in sys.path:
        sys.path.insert(0, str(cli_path))
    generate_plugin = import_module("entity.cli.plugin_tool.generate").generate_plugin
    load_plugin = import_module("entity.cli.plugin_tool.utils").load_plugin
    PLUGIN_TYPES = import_module("entity.cli.plugin_tool.main").PLUGIN_TYPES
=======
from entity.pipeline.exceptions import CircuitBreakerTripped
from entity.utils.logging import get_logger
from entity.config.environment import load_config
>>>>>>> pr-1793

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
<<<<<<< HEAD
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
        from entity.core.plugins.utils import PluginAutoClassifier

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
        else:
            logger.error("Unknown infrastructure type %s", typ)
            return 1
        await infra.deploy()
        return 0

    async def _infra_destroy(self, typ: str, path: str) -> int:
        if typ == "docker":
            infra = DockerInfrastructure({"path": path})
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
=======
>>>>>>> pr-1793
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
                            try:
                                v_result = await validate()
                                if not v_result.success:
                                    raise RuntimeError(v_result.message)
                            except Exception as exc:  # noqa: BLE001
                                logger.error(
                                    "Runtime validation failed for %s: %s",
                                    plugin_name,
                                    exc,
                                )
                                await p.rollback_config(p.config_version - 1)
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
