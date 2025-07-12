import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, fields

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "entity_config_models", ROOT / "src/entity/config/models.py"
)
models = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(models)


def iter_models() -> Iterable[type[BaseModel]]:
    for _, obj in inspect.getmembers(models):
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == models.__name__
        ):
            yield obj


def field_type_str(field: Any) -> str:
    t = getattr(field, "annotation", None) or getattr(field, "type_", None)
    return getattr(t, "__name__", str(t))


def default_str(field: Any) -> str:
    if hasattr(field, "is_required"):
        if field.is_required():
            return "Required"
    default = field.default
    if default is fields.PydanticUndefined:
        return "Required"
    return repr(default)


def model_section(model_cls: type[BaseModel]) -> str:
    lines = [f"## {model_cls.__name__}", ""]
    if model_cls.__doc__:
        lines.append(model_cls.__doc__.strip())
        lines.append("")
    lines.extend(
        [
            "| Field | Type | Default | Description |",
            "| --- | --- | --- | --- |",
        ]
    )
    for name, field in model_cls.model_fields.items():
        desc = getattr(field, "description", "") or ""
        lines.append(
            f"| {name} | {field_type_str(field)} | {default_str(field)} | {desc} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_docs() -> str:
    sections = ["# Configuration Reference", ""]
    for model_cls in iter_models():
        sections.append(model_section(model_cls))
    return "\n".join(sections).strip() + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="docs/source/config_reference.md")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = build_docs()
    path = Path(args.output)
    if args.check:
        if not path.exists() or path.read_text() != content:
            print(
                "Configuration docs are out of date. Run docs/generate_config_docs.py"
            )
            raise SystemExit(1)
        return
    path.write_text(content)


if __name__ == "__main__":
    main()
