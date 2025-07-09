from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Type

ROOT = Path(__file__).resolve().parent.parent  # noqa: E402
if str(ROOT) not in sys.path:  # noqa: E402
    sys.path.insert(0, str(ROOT))

from entity.core.plugins import BasePlugin  # noqa: E402
from entity.core.plugins import FailurePlugin  # noqa: E402
from entity.core.plugins import PromptPlugin  # noqa: E402
from entity.core.plugins import ResourcePlugin  # noqa: E402
from entity.core.plugins import ToolPlugin  # noqa: E402
from entity.core.plugins import AdapterPlugin, ValidationResult  # noqa: E402
from entity.utils.logging import get_logger  # noqa: E402

from .generate import generate_plugin  # noqa: E402
from .utils import load_plugin  # noqa: E402

PLUGIN_TYPES: dict[str, Type[BasePlugin]] = {
    "resource": ResourcePlugin,
    "tool": ToolPlugin,
    "prompt": PromptPlugin,
    "adapter": AdapterPlugin,
    "failure": FailurePlugin,
}

logger = get_logger(__name__)


@dataclass
class PluginToolArgs:
    """Arguments parsed for :class:`PluginToolCLI`."""

    command: str
    name: Optional[str] = None
    type: Optional[str] = None
    out: Optional[str] = None
    docs_dir: Optional[str] = None
    path: Optional[str] = None
    paths: Optional[list[str]] = None


class PluginToolCLI:
    """CLI utility for working with Entity plugins."""

    def __init__(self) -> None:
        self.args: PluginToolArgs = self._parse_args()

    def _parse_args(self) -> PluginToolArgs:
        parser = argparse.ArgumentParser(
            description="Helper tool for creating and validating Entity plugins"
        )
        sub = parser.add_subparsers(dest="command", required=True)

        gen = sub.add_parser("generate", help="Generate plugin boilerplate")
        gen.add_argument("name", help="Plugin name")
        gen.add_argument("--type", required=True, choices=list(PLUGIN_TYPES))
        gen.add_argument("--out", default="src", help="Output directory")
        gen.add_argument("--docs-dir", default="docs/source")

        val = sub.add_parser("validate", help="Validate plugin structure")
        val.add_argument("path", help="Path to plugin file")

        tst = sub.add_parser("test", help="Run plugin in isolation")
        tst.add_argument("path", help="Path to plugin file")

        cfg = sub.add_parser("config", help="Interactive configuration builder")
        cfg.add_argument("--name", required=True)
        cfg.add_argument("--type", required=True, choices=list(PLUGIN_TYPES))

        dep = sub.add_parser("deps", help="Analyze plugin dependencies")
        dep.add_argument("paths", nargs="+", help="Plugin module paths")

        doc = sub.add_parser("docs", help="Generate documentation for plugin")
        doc.add_argument("path", help="Plugin file path")
        doc.add_argument("--out", default="docs/source")

        ana = sub.add_parser(
            "analyze-plugin", help="Suggest pipeline stages for plugin functions"
        )
        ana.add_argument("path", help="Plugin file path")

        parsed = parser.parse_args()
        return PluginToolArgs(
            command=parsed.command,
            name=getattr(parsed, "name", None),
            type=getattr(parsed, "type", None),
            out=getattr(parsed, "out", None),
            docs_dir=getattr(parsed, "docs_dir", None),
            path=getattr(parsed, "path", None),
            paths=getattr(parsed, "paths", None),
        )

    # -----------------------------------------------------
    # command implementations
    # -----------------------------------------------------
    def run(self) -> int:
        cmd = self.args.command
        if cmd == "generate":
            return self._generate()
        if cmd == "validate":
            return self._validate()
        if cmd == "test":
            return self._test()
        if cmd == "config":
            return self._config()
        if cmd == "deps":
            return self._deps()
        if cmd == "docs":
            return self._docs()
        if cmd == "analyze-plugin":
            return self._analyze_plugin()
        return 0

    def _generate(self) -> int:
        assert self.args.name is not None
        assert self.args.type is not None
        assert self.args.out is not None
        assert self.args.docs_dir is not None
        return generate_plugin(
            self.args.name,
            self.args.type,
            Path(self.args.out),
            Path(self.args.docs_dir),
        )

    def _validate(self) -> int:
        assert self.args.path is not None
        plugin_cls = self._load_plugin(self.args.path)
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

    def _test(self) -> int:
        assert self.args.path is not None
        plugin_cls = self._load_plugin(self.args.path)
        instance = plugin_cls(getattr(plugin_cls, "config", {}))
        if hasattr(instance, "initialize") and callable(instance.initialize):
            logger.info("Initializing plugin...")
            import asyncio

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
                    import asyncio

                    asyncio.run(instance._execute_impl(ctx))
                else:
                    instance._execute_impl(ctx)
            except Exception as exc:  # pragma: no cover - manual testing
                logger.error("Execution failed: %s", exc)
                return 1
        logger.info("Plugin executed successfully")
        return 0

    def _config(self) -> int:
        assert self.args.name is not None
        assert self.args.type is not None
        name = self.args.name
        plugin_type = self.args.type
        cfg: dict[str, str] = {}
        logger.info("Building configuration for %s (%s)", name, plugin_type)
        while True:
            key = input("key (blank to finish): ").strip()
            if not key:
                break
            value = input(f"value for '{key}': ").strip()
            cfg[key] = value
        section = self._section_for_type(plugin_type)
        import yaml

        output = yaml.dump({"plugins": {section: {name: cfg}}})
        logger.info("\n%s", output)
        return 0

    def _deps(self) -> int:
        assert self.args.paths is not None
        paths: list[str] = self.args.paths
        for p in paths:
            cls = self._load_plugin(p)
            deps = getattr(cls, "dependencies", [])
            name = cls.__name__
            logger.info(
                "%s: %s",
                name,
                ", ".join(deps) if deps else "no dependencies",
            )
        return 0

    def _docs(self) -> int:
        assert self.args.path is not None
        assert self.args.out is not None
        cls = self._load_plugin(self.args.path)
        out_dir = Path(self.args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        name = cls.__name__.lower()
        doc_path = out_dir / f"{name}.md"
        doc = inspect.getdoc(cls) or cls.__name__
        doc_path.write_text(f"# {cls.__name__}\n\n{doc}\n")
        logger.info("Documentation written to %s", doc_path)
        return 0

    def _analyze_plugin(self) -> int:
        assert self.args.path is not None
        path = self.args.path
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

    # -----------------------------------------------------
    # helper methods
    # -----------------------------------------------------
    def _load_plugin(self, path: str) -> Type[BasePlugin]:
        return load_plugin(path)

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


def main() -> None:
    cli = PluginToolCLI()
    raise SystemExit(cli.run())


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
