from __future__ import annotations

from pathlib import Path

from entity.utils.logging import get_logger

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
logger = get_logger(__name__)


def generate_plugin(name: str, plugin_type: str, out_dir: Path, docs_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    class_name = "".join(part.capitalize() for part in name.split("_"))
    template_path = TEMPLATE_DIR / f"{plugin_type}.py"
    template = template_path.read_text()
    content = template.format(class_name=class_name)
    module_path = out_dir / f"{name}.py"
    module_path.write_text(content)

    docs_path = docs_dir / f"{name}.md"
    docs_path.write_text(f"## {class_name}\n\n.. automodule:: {name}\n    :members:\n")
    logger.info("Created %s", module_path)
    logger.info("Created %s", docs_path)
    return 0


__all__ = ["generate_plugin"]
