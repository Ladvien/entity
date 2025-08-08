"""Argument parsing resource for Entity framework CLI applications.

This resource provides structured argument parsing that follows Entity's 4-layer architecture
and integrates with the framework's logging and validation systems.
"""

import asyncio
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from entity.resources.logging import LogCategory, LoggingResource, LogLevel


class ArgumentType(Enum):
    """Supported argument types for Entity CLI parsing."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    PATH = "path"


class ArgumentCategory(Enum):
    """Categories for organizing CLI arguments."""

    WORKFLOW = "workflow"
    RESOURCE = "resource"
    OUTPUT = "output"
    SYSTEM = "system"


@dataclass
class ArgumentDefinition:
    """Definition of a command-line argument."""

    name: str
    type: ArgumentType
    category: ArgumentCategory
    help: str
    required: bool = False
    default: Any = None
    choices: Optional[List[str]] = None
    aliases: List[str] = field(default_factory=list)
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class CommandDefinition:
    """Definition of a CLI command with its arguments."""

    name: str
    help: str
    arguments: List[ArgumentDefinition] = field(default_factory=list)
    handler: Optional[Callable] = None


@dataclass
class ParsedArguments:
    """Result of argument parsing with structured data."""

    command: str
    values: Dict[str, Any] = field(default_factory=dict)
    raw_args: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


class ArgumentParsingResource(ABC):
    """Entity resource for structured CLI argument parsing.

    This resource follows Entity's patterns:
    - Uses structured logging via LoggingResource
    - Provides async validation and parsing
    - Maintains records for debugging
    - Integrates with Entity's resource acquisition pattern
    """

    def __init__(self, logger: Optional[LoggingResource] = None):
        self.logger = logger
        self.commands: Dict[str, CommandDefinition] = {}
        self.parsing_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def health_check(self) -> bool:
        """Resource health check."""
        return True

    async def log(self, level: LogLevel, category: LogCategory, message: str, **kwargs):
        """Log through Entity's logging system if available."""
        if self.logger:
            await self.logger.log(level, category, message, **kwargs)

    def register_command(self, command: CommandDefinition) -> None:
        """Register a command with the parser."""
        self.commands[command.name] = command

    def register_argument(
        self,
        command_name: str,
        name: str,
        type: ArgumentType,
        category: ArgumentCategory,
        help: str,
        **kwargs,
    ) -> None:
        """Register an argument for a specific command."""
        if command_name not in self.commands:
            self.commands[command_name] = CommandDefinition(
                name=command_name, help=f"Command: {command_name}"
            )

        arg_def = ArgumentDefinition(
            name=name, type=type, category=category, help=help, **kwargs
        )
        self.commands[command_name].arguments.append(arg_def)

    @abstractmethod
    async def parse(self, args: Optional[List[str]] = None) -> ParsedArguments:
        """Parse command-line arguments."""
        raise NotImplementedError

    @abstractmethod
    async def generate_help(self, command: Optional[str] = None) -> str:
        """Generate help text for commands."""
        raise NotImplementedError


class EntityArgumentParsingResource(ArgumentParsingResource):
    """Entity-native argument parsing implementation.

    Provides clean, structured argument parsing without external dependencies,
    following Entity framework patterns and integrating with Entity resources.
    """

    def __init__(
        self,
        logger: Optional[LoggingResource] = None,
        app_name: str = "entity-cli",
        app_description: str = "Entity Framework CLI",
    ):
        super().__init__(logger)
        self.app_name = app_name
        self.app_description = app_description

    async def parse(self, args: Optional[List[str]] = None) -> ParsedArguments:
        """Parse arguments using Entity-native parsing logic."""
        if args is None:
            args = sys.argv[1:]

        await self.log(
            LogLevel.DEBUG,
            LogCategory.USER_ACTION,
            "Starting argument parsing",
            args_count=len(args),
            app_name=self.app_name,
        )

        result = ParsedArguments(command="", raw_args=args.copy())

        if not args:
            result.validation_errors.append("No command provided")
            return result

        # Determine command
        potential_command = args[0]
        if potential_command.startswith("-"):
            # Handle global options
            result.command = "default"
        elif potential_command in self.commands:
            result.command = potential_command
            args = args[1:]  # Remove command from args
        else:
            result.command = "default"

        # Parse arguments for the identified command
        if result.command in self.commands:
            command_def = self.commands[result.command]
            parsed_values, errors = await self._parse_command_arguments(
                command_def, args
            )
            result.values = parsed_values
            result.validation_errors.extend(errors)

        # Store parsing history
        async with self._lock:
            self.parsing_history.append(
                {
                    "timestamp": sys.exec_prefix,  # Simple timestamp proxy
                    "command": result.command,
                    "args": args,
                    "success": len(result.validation_errors) == 0,
                }
            )

        await self.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            f"Parsed command: {result.command}",
            success=len(result.validation_errors) == 0,
            error_count=len(result.validation_errors),
        )

        return result

    async def _parse_command_arguments(
        self, command_def: CommandDefinition, args: List[str]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Parse arguments for a specific command."""
        values = {}
        errors = []
        args_iter = iter(args)

        # Set defaults
        for arg_def in command_def.arguments:
            if arg_def.default is not None:
                values[arg_def.name] = arg_def.default

        # Parse provided arguments
        while True:
            try:
                arg = next(args_iter)
            except StopIteration:
                break

            if not arg.startswith("-"):
                # Positional argument handling
                continue

            # Remove leading dashes
            arg_name = arg.lstrip("-")

            # Find matching argument definition
            arg_def = None
            for definition in command_def.arguments:
                if definition.name == arg_name or arg_name in definition.aliases:
                    arg_def = definition
                    break

            if not arg_def:
                errors.append(f"Unknown argument: {arg}")
                continue

            # Parse argument value
            if arg_def.type == ArgumentType.BOOLEAN:
                values[arg_def.name] = True
            else:
                try:
                    value_str = next(args_iter)
                    parsed_value = await self._convert_value(value_str, arg_def)
                    values[arg_def.name] = parsed_value
                except StopIteration:
                    errors.append(f"Missing value for argument: {arg}")
                except ValueError as e:
                    errors.append(f"Invalid value for {arg}: {e}")

        # Validate required arguments
        for arg_def in command_def.arguments:
            if arg_def.required and arg_def.name not in values:
                errors.append(f"Required argument missing: {arg_def.name}")

        # Run custom validators
        for arg_def in command_def.arguments:
            if arg_def.validator and arg_def.name in values:
                if not arg_def.validator(values[arg_def.name]):
                    errors.append(f"Validation failed for {arg_def.name}")

        return values, errors

    async def _convert_value(self, value_str: str, arg_def: ArgumentDefinition) -> Any:
        """Convert string value to appropriate type."""
        if arg_def.type == ArgumentType.STRING:
            return value_str
        elif arg_def.type == ArgumentType.INTEGER:
            return int(value_str)
        elif arg_def.type == ArgumentType.BOOLEAN:
            return value_str.lower() in ("true", "1", "yes", "on")
        elif arg_def.type == ArgumentType.CHOICE:
            if arg_def.choices and value_str not in arg_def.choices:
                raise ValueError(f"Must be one of: {', '.join(arg_def.choices)}")
            return value_str
        elif arg_def.type == ArgumentType.PATH:
            from pathlib import Path

            return Path(value_str)
        else:
            return value_str

    async def generate_help(self, command: Optional[str] = None) -> str:
        """Generate help text using Entity's structured approach."""
        if command and command in self.commands:
            return await self._generate_command_help(self.commands[command])
        else:
            return await self._generate_general_help()

    async def _generate_command_help(self, command_def: CommandDefinition) -> str:
        """Generate help for a specific command."""
        lines = [
            f"{self.app_name} {command_def.name}",
            "",
            command_def.help,
            "",
            "Arguments:",
        ]

        # Group arguments by category
        categories = {}
        for arg_def in command_def.arguments:
            cat = arg_def.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(arg_def)

        for category, args in categories.items():
            lines.append(f"  {category.title()}:")
            for arg_def in args:
                arg_line = f"    --{arg_def.name}"
                if arg_def.aliases:
                    arg_line += f", {', '.join(f'-{a}' for a in arg_def.aliases)}"
                if arg_def.type != ArgumentType.BOOLEAN:
                    arg_line += f" <{arg_def.type.value}>"
                lines.append(arg_line)
                lines.append(f"      {arg_def.help}")
                if arg_def.default is not None:
                    lines.append(f"      Default: {arg_def.default}")
                if arg_def.choices:
                    lines.append(f"      Choices: {', '.join(arg_def.choices)}")
            lines.append("")

        return "\n".join(lines)

    async def _generate_general_help(self) -> str:
        """Generate general help text."""
        lines = [f"{self.app_name} - {self.app_description}", "", "Available Commands:"]

        for name, command_def in self.commands.items():
            lines.append(f"  {name:<12} {command_def.help}")

        lines.extend(
            [
                "",
                f"Use '{self.app_name} <command> --help' for more information on a command.",
            ]
        )

        return "\n".join(lines)


# Factory function following Entity patterns
def create_argument_parsing_resource(
    logger: Optional[LoggingResource] = None,
    app_name: str = "entity-cli",
    app_description: str = "Entity Framework CLI",
) -> EntityArgumentParsingResource:
    """Factory function to create ArgumentParsingResource following Entity patterns."""
    return EntityArgumentParsingResource(
        logger=logger, app_name=app_name, app_description=app_description
    )
