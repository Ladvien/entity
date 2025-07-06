"""Command line interface for the debug dashboard."""

from __future__ import annotations

import argparse

from .logger import LogReplayer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug dashboard prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    replay_p = subparsers.add_parser("replay", help="Replay a state log")
    replay_p.add_argument("file", help="Log file to replay")
    replay_p.add_argument(
        "--delay", type=float, default=0.5, help="Delay between steps"
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "replay":
        LogReplayer(args.file).replay(args.delay)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
