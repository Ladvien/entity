"""Entity-native CLI implementation using ArgumentParsingResource.

This module provides a clean, Entity-idiomatic CLI that:
- Uses Entity's ArgumentParsingResource following the 4-layer architecture
- Integrates with Entity's logging system for structured feedback
- Follows the resources.get() acquisition pattern
- Maintains Entity's zero-config philosophy
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Dict, Optional

from entity.defaults import load_defaults
from entity.resources.argument_parsing import (
    ArgumentCategory,
    ArgumentType,
    ParsedArguments,
)
from entity.resources.logging import LogCategory, LogLevel

from .commands.init import init_command
from .commands.run import run_command


class EntityCLI:
    """Entity-native CLI using the framework's resource system."""

    def __init__(self):
        self.resources = load_defaults()
        self.arg_parser = self.resources.get("argument_parsing")
        self.logger = self.resources.get("logging")
        self._setup_commands()

    def _setup_commands(self):
        """Setup CLI commands using Entity's ArgumentParsingResource."""
        # Register init command
        self.arg_parser.register_argument(
            "init",
            "project_name",
            ArgumentType.STRING,
            ArgumentCategory.SYSTEM,
            "Name of the project (defaults to current directory name)",
            required=False,
        )
        self.arg_parser.register_argument(
            "init",
            "template",
            ArgumentType.CHOICE,
            ArgumentCategory.WORKFLOW,
            "Project template to use",
            default="basic",
            choices=["basic", "chatbot", "research", "code-review"],
        )
        self.arg_parser.register_argument(
            "init",
            "no-deps",
            ArgumentType.BOOLEAN,
            ArgumentCategory.SYSTEM,
            "Skip dependency installation",
            aliases=["no-deps"],
        )
        self.arg_parser.register_argument(
            "init",
            "quiet",
            ArgumentType.BOOLEAN,
            ArgumentCategory.OUTPUT,
            "Minimal output",
            aliases=["q"],
        )

        # Register run command
        self.arg_parser.register_argument(
            "run",
            "workflow",
            ArgumentType.STRING,
            ArgumentCategory.WORKFLOW,
            "Workflow template name or YAML path",
            default="default",
        )
        self.arg_parser.register_argument(
            "run",
            "verbose",
            ArgumentType.BOOLEAN,
            ArgumentCategory.OUTPUT,
            "Enable debug logging",
            aliases=["v"],
        )
        self.arg_parser.register_argument(
            "run",
            "quiet",
            ArgumentType.BOOLEAN,
            ArgumentCategory.OUTPUT,
            "Suppress informational logs",
            aliases=["q"],
        )
        self.arg_parser.register_argument(
            "run",
            "timeout",
            ArgumentType.INTEGER,
            ArgumentCategory.SYSTEM,
            "Maximum seconds to wait for completion",
        )

    async def run(self, argv: Optional[list[str]] = None) -> int:
        """Run the CLI with Entity-native argument parsing."""
        try:
            await self.logger.log(
                LogLevel.DEBUG,
                LogCategory.USER_ACTION,
                "Entity CLI starting",
                args=argv or sys.argv[1:],
            )

            # Parse arguments using Entity's ArgumentParsingResource
            parsed = await self.arg_parser.parse(argv)

            if parsed.validation_errors:
                await self.logger.log(
                    LogLevel.ERROR,
                    LogCategory.ERROR,
                    "Argument parsing failed",
                    errors=parsed.validation_errors,
                )
                await self._show_help_and_errors(parsed)
                return 1

            # Handle help requests
            if "--help" in (argv or sys.argv[1:]) or "-h" in (argv or sys.argv[1:]):
                help_text = await self.arg_parser.generate_help(parsed.command)
                print(help_text)
                return 0

            # Handle version requests
            if "--version" in (argv or sys.argv[1:]):
                print("entity-cli 0.0.5")
                return 0

            # Execute command
            return await self._execute_command(parsed)

        except KeyboardInterrupt:
            await self.logger.log(
                LogLevel.INFO, LogCategory.USER_ACTION, "CLI interrupted by user"
            )
            return 130
        except Exception as exc:
            await self.logger.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                "CLI execution failed",
                error=str(exc),
            )
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    async def _execute_command(self, parsed: ParsedArguments) -> int:
        """Execute the parsed command using Entity patterns."""
        await self.logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            f"Executing command: {parsed.command}",
            values=parsed.values,
        )

        # Create a simple namespace-like object for backward compatibility
        class Args:
            def __init__(self, values: Dict[str, Any], command: str):
                self.__dict__.update(values)
                self.command = command

        args = Args(parsed.values, parsed.command)

        # Route to command handlers
        if parsed.command == "init":
            args.func = init_command
            await init_command(args)
            return 0
        elif parsed.command == "run" or parsed.command == "default":
            args.func = run_command
            await run_command(args)
            return 0
        else:
            await self.logger.log(
                LogLevel.ERROR, LogCategory.ERROR, f"Unknown command: {parsed.command}"
            )
            help_text = await self.arg_parser.generate_help()
            print(help_text)
            return 1

    async def _show_help_and_errors(self, parsed: ParsedArguments):
        """Show help text and validation errors using Entity's logging."""
        # Show errors first
        for error in parsed.validation_errors:
            await self.logger.log(
                LogLevel.ERROR, LogCategory.ERROR, f"Argument error: {error}"
            )

        # Show help
        help_text = await self.arg_parser.generate_help(
            parsed.command if parsed.command else None
        )
        print(f"\n{help_text}")


async def main_async(argv: Optional[list[str]] = None) -> int:
    """Main async entry point using Entity's resource system."""
    cli = EntityCLI()
    return await cli.run(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Main synchronous entry point for the Entity CLI."""
    exit_code = asyncio.run(main_async(argv))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
