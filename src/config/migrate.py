from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from config.models import EntityConfig, asdict
from pipeline.config import ConfigLoader


class ConfigMigrator:
    """CLI for migrating configuration files to the latest schema."""

    def __init__(self) -> None:
        self.args = self._parse_args()

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Migrate an Entity configuration file to the latest schema"
        )
        parser.add_argument("src", help="Existing configuration file")
        parser.add_argument(
            "dest",
            nargs="?",
            default="-",
            help="Output path or '-' for stdout",
        )
        return parser.parse_args()

    def run(self) -> int:
        data = ConfigLoader.from_yaml(self.args.src)
        config = EntityConfig.from_dict(data)
        text = yaml.safe_dump(asdict(config), sort_keys=False)
        if self.args.dest == "-":
            print(text)
        else:
            out = Path(self.args.dest)
            out.write_text(text)
            print(f"Wrote migrated config to {out}")
        return 0


def main() -> None:
    raise SystemExit(ConfigMigrator().run())


if __name__ == "__main__":
    main()
