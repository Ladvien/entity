"""Generate starter YAML configuration files."""

from __future__ import annotations

import argparse
from pathlib import Path

from entity.utils.logging import get_logger
from plugins.builtin.adapters.logging_adapter import configure_logging

logger = get_logger(__name__)


def main() -> int:
    configure_logging()

    parser = argparse.ArgumentParser(description="Generate a starter configuration")
    parser.add_argument(
        "path", nargs="?", default="-", help="Output path or '-' for stdout"
    )
    args = parser.parse_args()

    template = Path(__file__).resolve().parents[2] / "config" / "template.yaml"
    content = template.read_text()

    if args.path == "-":
        logger.info(content)
    else:
        dest = Path(args.path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        logger.info("Wrote template to %s", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
