import argparse
import asyncio
import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import yaml  # noqa: E402

from config.environment import load_env  # noqa: E402
from pipeline import SystemInitializer  # noqa: E402
from pipeline.config import ConfigLoader  # noqa: E402
from pipeline.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger(__name__)


class ConfigValidator:
    """CLI for validating Entity configuration files."""

    def __init__(self) -> None:
        self.args = self._parse_args()

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
        return parser.parse_args()

    def run(self) -> int:
        configure_logging()
        try:
            with Path(self.args.config).open("r") as fh:
                config = yaml.safe_load(fh) or {}
            load_env()
            config = ConfigLoader.from_dict(config)
            self._validate_memory(config)
            self._validate_cache(config)
            self._validate_vector_memory(config)
            initializer = SystemInitializer(config)
            asyncio.run(initializer.initialize())
        except Exception as exc:  # pragma: no cover - error path
            print(f"Configuration invalid: {exc}")
            logger.error("Configuration invalid: %s", exc)
            return 1
        print("Configuration valid")
        logger.info("Configuration valid.")
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
