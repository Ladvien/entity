"""Configuration helpers for Entity."""

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

from pydantic import ValidationError  # noqa: E402

from pipeline import SystemInitializer  # noqa: E402
from pipeline.config import ConfigLoader  # noqa: E402
from entity.utils.logging import get_logger  # noqa: E402
from plugins.builtin.adapters.logging_adapter import configure_logging  # noqa: E402

from .models import EntityConfig, asdict  # noqa: E402

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
                data = ConfigLoader.from_yaml(cfg_path)
                config_model = EntityConfig.from_dict(data)
                initializer = SystemInitializer(asdict(config_model))
                asyncio.run(initializer.initialize())
            except ValidationError as exc:  # pragma: no cover - error path
                logger.error("Configuration invalid: %s", exc)
                print(f"Configuration invalid: {exc}")
                return False
            except Exception as exc:  # pragma: no cover - error path
                logger.error("Configuration invalid: %s", exc)
                print(f"Configuration invalid: {exc}")
                return False
            logger.info("Configuration valid.")
            print("Configuration valid")
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
        else:
            return 1
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
                    logger.error("Rolled back to last valid configuration")

        return 0


def main() -> None:
    raise SystemExit(ConfigValidator().run())


if __name__ == "__main__":
    main()
