from __future__ import annotations

from pathlib import Path

from entity.utils.logging import get_logger

logger = get_logger(__name__)


_PLUGIN_TYPES = {"adapter", "failure", "prompt", "resource", "tool"}


def _class_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def generate_plugin(name: str, ptype: str, out_dir: Path, docs_dir: Path) -> int:
    """Generate plugin source and docs from templates.

    Parameters
    ----------
    name:
        Plugin name (and file base name).
    ptype:
        Plugin type: one of ``adapter``, ``failure``, ``prompt``, ``resource`` or
        ``tool``.
    out_dir:
        Directory for the generated plugin file.
    docs_dir:
        Directory for the generated documentation file.
    """
    if ptype not in _PLUGIN_TYPES:
        logger.error("Invalid plugin type: %s", ptype)
        return 1

    plugin_file = out_dir / f"{name}.py"
    doc_file = docs_dir / f"{name}.md"
    if plugin_file.exists() or doc_file.exists():
        logger.error("%s or %s already exists", plugin_file, doc_file)
        return 1

    template_dir = Path("templates/plugins")
    template_path = template_dir / f"{ptype}.py"
    if not template_path.exists():
        logger.error("Template not found for %s", ptype)
        return 1

    class_name = _class_name(name)
    plugin_code = template_path.read_text().replace("CLASS_NAME", class_name)

    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    plugin_file.write_text(plugin_code)
    doc_file.write_text(f"## {class_name}\n\n.. automodule:: {name}\n    :members:\n")

    logger.info("Created plugin at %s", plugin_file)
    logger.info("Created docs at %s", doc_file)
    return 0
