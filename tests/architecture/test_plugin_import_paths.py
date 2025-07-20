import ast
from pathlib import Path

DISALLOWED_PREFIXES = (
    "entity.core.pipeline",
    "entity.core.agent",
)

ALLOWED_CORE_PREFIXES = (
    "entity.plugins.base",
    "entity.resources",
    "entity.utils",
)


def _resolve(module_name: str, target: str, level: int) -> str:
    if level == 0:
        return target
    package_parts = module_name.split(".")[:-1]
    up = min(level, len(package_parts))
    prefix = package_parts[:-up]
    if not prefix:
        prefix = ["entity"]
    resolved = ".".join(prefix)
    if target:
        resolved += f".{target}"
    return resolved


def _imports(path: Path, module_name: str) -> list[str]:
    tree = ast.parse(path.read_text())
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(_resolve(module_name, node.module or "", node.level))
    return imports


def test_plugins_do_not_import_disallowed_core_modules() -> None:
    plugin_dirs = [Path("src/entity/plugins"), Path("src/plugins")]
    offenses: list[str] = []
    for base in plugin_dirs:
        if not base.exists():
            continue
        for file in base.rglob("*.py"):
            module = file.with_suffix("").as_posix().replace("/", ".")
            if module.startswith("src."):
                module = module[4:]
            imports = _imports(file, module)
            for imp in imports:
                if imp.startswith(DISALLOWED_PREFIXES):
                    offenses.append(f"{file}:{imp}")
    assert not offenses, "Disallowed imports found:\n" + "\n".join(offenses)
