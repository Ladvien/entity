#!/usr/bin/env python3
"""Multi-Modal Research Assistant - Entity Framework Example with Entity-native CLI."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from entity import Agent
from entity.defaults import load_defaults
from entity.resources.argument_parsing import ArgumentCategory, ArgumentType
from entity.resources.logging import LogCategory, LogLevel


class ResearchAssistantCLI:
    """Entity-native CLI for the research assistant."""

    def __init__(self):
        self.resources = load_defaults()
        self.logger = self.resources.get("logging")
        self.arg_parser = self.resources.get("argument_parsing")
        self.agent = None
        self._setup_commands()

    def _setup_commands(self):
        """Setup CLI commands using Entity's ArgumentParsingResource."""
        # Research command
        self.arg_parser.register_argument(
            "research",
            "query",
            ArgumentType.STRING,
            ArgumentCategory.WORKFLOW,
            "Research query or topic",
            required=True,
        )
        self.arg_parser.register_argument(
            "research",
            "pdf",
            ArgumentType.PATH,
            ArgumentCategory.WORKFLOW,
            "PDF file to analyze alongside the query",
        )
        self.arg_parser.register_argument(
            "research",
            "sources",
            ArgumentType.STRING,
            ArgumentCategory.RESOURCE,
            "Comma-separated list of sources",
            default="arxiv,web",
        )
        self.arg_parser.register_argument(
            "research",
            "output-format",
            ArgumentType.CHOICE,
            ArgumentCategory.OUTPUT,
            "Output format for the research report",
            default="academic",
            choices=["academic", "executive", "blog"],
        )
        self.arg_parser.register_argument(
            "research",
            "max-papers",
            ArgumentType.INTEGER,
            ArgumentCategory.RESOURCE,
            "Maximum number of papers to analyze",
            default=20,
        )
        self.arg_parser.register_argument(
            "research",
            "config",
            ArgumentType.PATH,
            ArgumentCategory.SYSTEM,
            "Path to configuration file",
            default="research_config.yaml",
        )

    async def run(self, argv: Optional[list[str]] = None) -> int:
        """Run the CLI using Entity's resource system."""
        try:
            parsed = await self.arg_parser.parse(argv)

            if parsed.validation_errors:
                for error in parsed.validation_errors:
                    await self.logger.log(
                        LogLevel.ERROR, LogCategory.ERROR, f"Argument error: {error}"
                    )
                help_text = await self.arg_parser.generate_help()
                print(help_text)
                return 1

            # Handle help
            if (
                "--help" in (argv or sys.argv[1:])
                or not parsed.command
                or parsed.command == "default"
            ):
                help_text = await self.arg_parser.generate_help("research")
                print(help_text)
                return 0

            # Initialize agent and execute research
            await self._initialize_agent(parsed.values)
            return await self._handle_research(parsed.values)

        except KeyboardInterrupt:
            await self.logger.log(
                LogLevel.INFO, LogCategory.USER_ACTION, "Research session ended by user"
            )
            return 0
        except Exception as exc:
            await self.logger.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                "Research assistant error",
                error=str(exc),
            )
            print(f"\n❌ Unexpected error: {exc}")
            return 1

    async def _initialize_agent(self, args: dict):
        """Initialize the Entity agent with configuration."""
        try:
            config_path = Path(args.get("config", "research_config.yaml"))

            await self.logger.log(
                LogLevel.INFO,
                LogCategory.RESOURCE_ACCESS,
                "Initializing research assistant agent",
                config_file=str(config_path),
            )

            if config_path.exists():
                self.agent = Agent.from_config(str(config_path))
                await self.logger.log(
                    LogLevel.INFO,
                    LogCategory.USER_ACTION,
                    "Loaded agent from configuration file",
                    config_path=str(config_path),
                )
            else:
                self.agent = Agent.from_workflow("research_assistant")
                await self.logger.log(
                    LogLevel.INFO,
                    LogCategory.USER_ACTION,
                    "Using default research assistant workflow",
                )

        except Exception as exc:
            await self.logger.log(
                LogLevel.ERROR,
                LogCategory.ERROR,
                "Failed to initialize research assistant",
                error=str(exc),
            )
            raise

    async def _handle_research(self, args: dict) -> int:
        """Handle the research command using Entity patterns."""
        query = args["query"]
        sources = args.get("sources", "arxiv,web").split(",")
        output_format = args.get("output-format", "academic")
        max_papers = args.get("max-papers", 20)
        pdf_path = args.get("pdf")

        # Prepare research context
        research_context = {
            "query": query,
            "sources": sources,
            "output_format": output_format,
            "max_papers": max_papers,
        }

        if pdf_path and Path(pdf_path).exists():
            research_context["pdf_path"] = str(Path(pdf_path).absolute())

        await self.logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Starting research",
            query=query,
            sources=sources,
            output_format=output_format,
            max_papers=max_papers,
            has_pdf=pdf_path is not None,
        )

        # Store research context in memory for plugins to access
        await self.agent.remember("research_context", research_context)

        # Display research parameters
        print(f"\n🔬 Starting research on: {query}")
        print(f"📚 Sources: {', '.join(sources)}")
        print(f"📊 Max papers: {max_papers}")
        if pdf_path:
            print(f"📄 Analyzing PDF: {Path(pdf_path).name}")
        print("\n" + "=" * 60 + "\n")

        # Execute research
        response = await self.agent.chat(query)

        # Display results
        print("\n" + "=" * 60)
        print("📝 RESEARCH REPORT")
        print("=" * 60 + "\n")
        print(response)

        # Save report to file
        output_file = Path(f"research_report_{output_format}.md")
        output_file.write_text(response)

        await self.logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Research completed successfully",
            output_file=str(output_file),
            response_length=len(response),
        )

        print(f"\n✅ Report saved to: {output_file}")
        return 0


async def main_async() -> int:
    """Main async entry point using Entity patterns."""
    cli = ResearchAssistantCLI()
    return await cli.run()


def main():
    """Main entry point following Entity's async patterns."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
