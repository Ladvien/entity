import argparse
import asyncio
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from config.environment import load_env  # noqa: E402
from pipeline import SystemInitializer  # noqa: E402


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
            initializer = SystemInitializer(config)
            asyncio.run(initializer.initialize())
        except Exception as exc:  # pragma: no cover - error path
            print(f"Configuration invalid: {exc}")
            return 1
        print("Configuration valid.")
        return 0


def main() -> None:
    raise SystemExit(ConfigValidator().run())


if __name__ == "__main__":
    main()
