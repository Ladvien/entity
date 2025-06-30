import argparse
import asyncio
from pathlib import Path

import yaml

from src.config.environment import load_env  # noqa: E402
from src.pipeline import SystemInitializer  # noqa: E402


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
        try:
            with Path(self.args.config).open("r") as fh:
                config = yaml.safe_load(fh) or {}
            load_env()
            config = SystemInitializer._interpolate_env_vars(config)
            self._validate_vector_memory(config)
            initializer = SystemInitializer(config)
            asyncio.run(initializer.initialize())
        except Exception as exc:  # pragma: no cover - error path
            print(f"Configuration invalid: {exc}")
            return 1
        print("Configuration valid.")
        return 0

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


def main() -> None:
    raise SystemExit(ConfigValidator().run())


if __name__ == "__main__":
    main()
