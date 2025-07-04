"""Generate starter YAML configuration files."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a starter configuration")
    parser.add_argument(
        "path", nargs="?", default="-", help="Output path or '-' for stdout"
    )
    args = parser.parse_args()

    template = Path(__file__).resolve().parents[2] / "config" / "template.yaml"
    content = template.read_text()

    if args.path == "-":
        print(content)
    else:
        dest = Path(args.path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        print(f"Wrote template to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
