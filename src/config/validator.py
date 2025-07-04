import argparse
import asyncio
import difflib
import sys
import time
from datetime import datetime
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import yaml  # noqa: E402
from jsonschema import RefResolver, ValidationError, validate  # noqa: E402

from config.environment import load_env  # noqa: E402
from pipeline import SystemInitializer  # noqa: E402
from pipeline.config import ConfigLoader  # noqa: E402
from pipeline.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger(__name__)


class ConfigValidator:
    """CLI for validating Entity configuration files."""

    def __init__(self) -> None:
        self.args = self._parse_args()
        schema_path = Path(__file__).resolve().parent / "schemas" / "config.yaml"
        self.schema = yaml.safe_load(schema_path.read_text())
        base_uri = f"file://{schema_path.parent}/"

        def yaml_loader(uri: str) -> object:
            path = Path(uri.replace("file://", ""))
            return yaml.safe_load(path.read_text())

        self.resolver = RefResolver(
            base_uri, self.schema, handlers={"file": yaml_loader}
        )

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Validate an Entity YAML configuration file."
        )
        parser.add_argument(
            "--config",
            "-c",
            required=True,
            help="Path to configuration file",
        )
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Watch the file and revalidate on changes",
        )
        return parser.parse_args()

    def run(self) -> int:
        configure_logging()

        cfg_path = Path(self.args.config)
        backups = Path("config/backups")
        backups.mkdir(parents=True, exist_ok=True)
        last_good = None

        def validate_once() -> bool:
            try:
                with cfg_path.open("r") as fh:
                    raw = yaml.safe_load(fh) or {}
                validate(instance=raw, schema=self.schema, resolver=self.resolver)
                load_env()
                config = ConfigLoader.from_dict(raw)
                self._validate_memory(config)
                self._validate_cache(config)
                self._validate_vector_memory(config)
                initializer = SystemInitializer(config)
                asyncio.run(initializer.initialize())
            except (ValidationError, Exception) as exc:  # pragma: no cover - error path
                print(f"Configuration invalid: {exc}")
                logger.error("Configuration invalid: %s", exc)
                return False
            print("Configuration valid")
            logger.info("Configuration valid.")
            return True

        def backup(prev_text: str | None, new_text: str) -> None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            bak_file = backups / f"{timestamp}.yaml"
            bak_file.write_text(new_text)
            if prev_text is not None:
                diff = difflib.unified_diff(
                    prev_text.splitlines(True),
                    new_text.splitlines(True),
                    "previous",
                    "current",
                )
                (backups / f"{timestamp}.diff").write_text("".join(diff))

        if not self.args.watch:
            success = validate_once()
            if success:
                backup(None, cfg_path.read_text())
            return 0 if success else 1

        # watch mode
        last_mtime = cfg_path.stat().st_mtime
        text = cfg_path.read_text()
        if validate_once():
            backup(None, text)
            last_good = text
        while True:
            time.sleep(1)
            mtime = cfg_path.stat().st_mtime
            if mtime == last_mtime:
                continue
            last_mtime = mtime
            new_text = cfg_path.read_text()
            if validate_once():
                backup(last_good, new_text)
                last_good = new_text
            else:
                if last_good is not None:
                    cfg_path.write_text(last_good)
                    print("Rolled back to last valid configuration")

        return 0

    def _validate_memory(self, config: dict) -> None:
        """Validate nested memory configuration."""

        mem_cfg = config.get("plugins", {}).get("resources", {}).get("memory")
        if not mem_cfg:
            return

        backend = mem_cfg.get("backend")
        if backend is not None and not isinstance(backend, dict):
            raise ValueError("memory: 'backend' must be a mapping")
        if isinstance(backend, dict) and "type" in backend:
            if not isinstance(backend["type"], str):
                raise ValueError("memory: 'backend.type' must be a string")

    def _validate_vector_memory(self, config: dict) -> None:
        """Ensure vector memory configuration contains required fields."""

        vm_cfg = config.get("plugins", {}).get("resources", {}).get("vector_memory")
        if not vm_cfg:
            return

        table = vm_cfg.get("table")
        if not isinstance(table, str) or not table:
            raise ValueError("vector_memory: 'table' is required")

        embedding = vm_cfg.get("embedding_model")
        if not isinstance(embedding, dict):
            raise ValueError("vector_memory: 'embedding_model' must be a mapping")

        if not embedding.get("name"):
            raise ValueError("vector_memory: 'embedding_model.name' is required")

        if "dimensions" in embedding:
            try:
                int(embedding["dimensions"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "vector_memory: 'embedding_model.dimensions' must be an integer"
                ) from exc

    def _validate_cache(self, config: dict) -> None:
        """Validate optional cache configuration."""

        cache_cfg = config.get("plugins", {}).get("resources", {}).get("cache")
        if not cache_cfg:
            return

        backend = cache_cfg.get("backend")
        if backend is not None and not isinstance(backend, dict):
            raise ValueError("cache: 'backend' must be a mapping")
        if isinstance(backend, dict) and "type" in backend:
            if not isinstance(backend["type"], str):
                raise ValueError("cache: 'backend.type' must be a string")


def main() -> None:
    raise SystemExit(ConfigValidator().run())


if __name__ == "__main__":
    main()
