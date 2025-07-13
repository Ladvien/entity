import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

stages_spec = importlib.util.spec_from_file_location(
    "entity.pipeline.stages", ROOT / "src/entity/pipeline/stages.py"
)
stages_mod = importlib.util.module_from_spec(stages_spec)
assert stages_spec.loader
stages_spec.loader.exec_module(stages_mod)
sys.modules["entity"] = importlib.util.module_from_spec(
    importlib.util.spec_from_loader("entity", loader=None)
)
pipeline_pkg = importlib.util.module_from_spec(
    importlib.util.spec_from_loader("entity.pipeline", loader=None)
)
sys.modules["entity.pipeline"] = pipeline_pkg
sys.modules["entity.pipeline.stages"] = stages_mod

spec = importlib.util.spec_from_file_location(
    "entity_config_models", ROOT / "src/entity/config/models.py"
)
models = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = models
spec.loader.exec_module(models)


def iter_models() -> Iterable[type[BaseModel]]:
    for _, obj in models.__dict__.items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == models.__name__
        ):
            yield obj


def build_schema() -> dict[str, dict]:
    """Return JSON schema for all configuration models."""
    schemas: dict[str, dict] = {}
    for m in iter_models():
        try:
            if hasattr(m, "model_rebuild"):
                m.model_rebuild(force=True)
            else:
                m.update_forward_refs()
        except Exception:
            pass
        try:
            schema = m.model_json_schema()
        except AttributeError:
            schema = m.schema()  # type: ignore[attr-defined]
        schemas[m.__name__] = schema
    return schemas


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="docs/source/config_schema.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = json.dumps(build_schema(), indent=2, sort_keys=True)
    path = Path(args.output)
    if args.check:
        if not path.exists() or path.read_text() != content:
            print(
                "Configuration schema is out of date. Run docs/generate_config_docs.py"
            )
            raise SystemExit(1)
        return
    path.write_text(content)


if __name__ == "__main__":
    main()
