from __future__ import annotations

import argparse
import asyncio
import sys

from .commands.init import add_init_parser
from .commands.run import add_run_parser, run_command


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments with subcommands."""
    parser = argparse.ArgumentParser(
        prog="entity", description="Entity Framework - Build powerful AI agents"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.0.5")

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="<command>"
    )

    add_init_parser(subparsers)
    add_run_parser(subparsers)

    args_to_check = argv if argv is not None else sys.argv[1:]

    if (
        args_to_check
        and args_to_check[0] in ["init", "run"]
        and not args_to_check[0].startswith("-")
    ):
        args = parser.parse_args(argv)
    else:
        if "--help" in args_to_check or "-h" in args_to_check:
            parser.print_help()
            sys.exit(0)
        elif "--version" in args_to_check:
            parser.print_version()
            sys.exit(0)
        else:
            legacy_parser = argparse.ArgumentParser(
                description="Run an Entity workflow locally with automatic resource setup"
            )
            legacy_parser.add_argument(
                "--workflow",
                default="default",
                help="Workflow template name or YAML path",
            )
            legacy_parser.add_argument(
                "-v",
                "--verbose",
                action="store_true",
                help="Enable debug logging",
            )
            legacy_parser.add_argument(
                "-q",
                "--quiet",
                action="store_true",
                help="Suppress informational logs",
            )
            legacy_parser.add_argument(
                "--timeout",
                type=int,
                default=None,
                help="Maximum seconds to wait for the workflow to complete",
            )
            args = legacy_parser.parse_args(argv)
            args.func = run_command

    return args


async def main_async(args: argparse.Namespace) -> None:
    """Execute the selected command asynchronously."""
    if hasattr(args, "func"):
        if asyncio.iscoroutinefunction(args.func):
            await args.func(args)
        else:
            args.func(args)
    else:
        print(
            "No command specified. Use --help to see available commands.",
            file=sys.stderr,
        )
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the Entity CLI."""
    args = parse_args(argv)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
