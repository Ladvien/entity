from __future__ import annotations

import argparse
import importlib.util
import inspect
from pathlib import Path
from typing import Any, Dict, List, Type

from pipeline.base_plugins import (
    AdapterPlugin,
    BasePlugin,
    FailurePlugin,
    PromptPlugin,
    ResourcePlugin,
    ToolPlugin,
    ValidationResult,
)
from pipeline.logging import get_logger

TEMPLATE_DIR = Path(__file__).parent / "templates"

PLUGIN_TYPES = {
    "resource": ResourcePlugin,
    "tool": ToolPlugin,
    "prompt": PromptPlugin,
    "adapter": AdapterPlugin,
    "failure": FailurePlugin,
}

logger = get_logger(__name__)


class PluginToolCLI:
    """CLI utility for working with Entity plugins."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
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

        return parser.parse_args()

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
        return 0

    def _generate(self) -> int:
        name = self.args.name
        plugin_type = self.args.type
        out_dir = Path(self.args.out)
        docs_dir = Path(self.args.docs_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)

        class_name = "".join(part.capitalize() for part in name.split("_"))
        template_path = TEMPLATE_DIR / f"{plugin_type}.py"
        template = template_path.read_text()
        content = template.format(class_name=class_name)
        module_path = out_dir / f"{name}.py"
        module_path.write_text(content)

        docs_path = docs_dir / f"{name}.md"
        docs_path.write_text(
            f"## {class_name}\n\n.. automodule:: {name}\n    :members:\n"
        )
        logger.info("Created %s", module_path)
        logger.info("Created %s", docs_path)
        return 0

    def _validate(self) -> int:
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
        plugin_cls = self._load_plugin(self.args.path)
        instance = plugin_cls(getattr(plugin_cls, "config", {}))
        if hasattr(instance, "initialize") and callable(instance.initialize):
            logger.info("Initializing plugin...")
            import asyncio

            asyncio.run(instance.initialize())
        if hasattr(instance, "_execute_impl"):
            logger.info("Executing plugin...")

            class DummyContext:
                async def __getattr__(self, _):
                    async def _noop(*_a, **_kw):
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
        name = self.args.name
        plugin_type = self.args.type
        cfg: Dict[str, Any] = {}
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
        paths: List[str] = self.args.paths
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
        cls = self._load_plugin(self.args.path)
        out_dir = Path(self.args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        name = cls.__name__.lower()
        doc_path = out_dir / f"{name}.md"
        doc = inspect.getdoc(cls) or cls.__name__
        doc_path.write_text(f"# {cls.__name__}\n\n{doc}\n")
        logger.info("Documentation written to %s", doc_path)
        return 0

    # -----------------------------------------------------
    # helper methods
    # -----------------------------------------------------
    def _load_plugin(self, path: str) -> Type[BasePlugin]:
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
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
            ):
                return obj
        raise RuntimeError("No plugin class found")

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
