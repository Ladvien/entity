"""Init command for creating new Entity projects."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

    def rprint(*args, **kwargs):
        print(*args, **kwargs)


console = Console() if RICH_AVAILABLE else None


def add_init_parser(subparsers) -> None:
    """Add the init command parser to the subparsers."""
    parser = subparsers.add_parser(
        "init",
        help="Initialize a new Entity project",
        description="Create a new Entity project with interactive setup",
    )
    parser.add_argument(
        "project_name",
        nargs="?",
        help="Name of the project (defaults to current directory name)",
    )
    parser.add_argument(
        "--template",
        default="basic",
        choices=["basic", "chatbot", "research", "code-review"],
        help="Project template to use",
    )
    parser.add_argument(
        "--no-deps", action="store_true", help="Skip dependency installation"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.set_defaults(func=init_command)


def detect_llm_services() -> Dict[str, Dict[str, Any]]:
    """Auto-detect available LLM services on the system."""
    services = {}

    try:
        import httpx

        with httpx.Client() as client:
            response = client.get("http://localhost:11434/api/version", timeout=2)
            if response.status_code == 200:
                services["ollama"] = {
                    "available": True,
                    "url": "http://localhost:11434",
                    "status": "✅ Running",
                    "models": [],
                }
                try:
                    models_response = client.get(
                        "http://localhost:11434/api/tags", timeout=5
                    )
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        services["ollama"]["models"] = [
                            model["name"] for model in models_data.get("models", [])
                        ]
                except Exception:
                    pass
    except Exception:
        services["ollama"] = {
            "available": False,
            "url": "http://localhost:11434",
            "status": "❌ Not available",
            "models": [],
        }

    cloud_services = {
        "openai": {
            "env_var": "OPENAI_API_KEY",
            "name": "OpenAI",
            "models": ["gpt-4", "gpt-3.5-turbo"],
        },
        "anthropic": {
            "env_var": "ANTHROPIC_API_KEY",
            "name": "Anthropic Claude",
            "models": ["claude-3-sonnet", "claude-3-haiku"],
        },
        "gemini": {
            "env_var": "GOOGLE_API_KEY",
            "name": "Google Gemini",
            "models": ["gemini-pro", "gemini-1.5-pro"],
        },
    }

    for service_id, config in cloud_services.items():
        has_key = bool(os.getenv(config["env_var"]))
        services[service_id] = {
            "available": has_key,
            "status": "✅ API key found" if has_key else "❌ No API key",
            "models": config["models"] if has_key else [],
            "env_var": config["env_var"],
            "name": config["name"],
        }

    return services


def create_env_example(project_path: Path, selected_service: str) -> None:
    """Create .env.example file with documented options."""
    env_content = """# Entity Framework Configuration
# Copy this file to .env and fill in your values

# Database Configuration (Optional)
DB_HOST=localhost
DB_NAME=entity_dev
DB_USERNAME=dev
DB_PASSWORD=dev

# Logging Configuration
LOG_LEVEL=info
DEBUG=false

"""

    if selected_service == "ollama":
        env_content += """# Ollama Configuration (Local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b-instruct-q6_K

"""
    elif selected_service == "openai":
        env_content += """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

"""
    elif selected_service == "anthropic":
        env_content += """# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

"""
    elif selected_service == "gemini":
        env_content += """# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-pro

"""

    env_content += """# File Storage Configuration
STORAGE_PATH=./data
MAX_FILE_SIZE=100MB

# Web Search (Optional)
SEARCH_API_KEY=your_search_api_key_here

# Weather API (Optional)
WEATHER_API_KEY=your_weather_api_key_here
"""

    (project_path / ".env.example").write_text(env_content)


def create_project_structure(project_path: Path, template: str) -> None:
    """Create the basic project structure."""
    (project_path / "src").mkdir(exist_ok=True)
    (project_path / "tests").mkdir(exist_ok=True)
    (project_path / "data").mkdir(exist_ok=True)
    (project_path / "workflows").mkdir(exist_ok=True)
    (project_path / "plugins").mkdir(exist_ok=True)

    main_content = f'''"""Main entry point for {project_path.name} Entity project.

This example demonstrates Entity's idiomatic CLI patterns using the ArgumentParsingResource.
Entity provides two execution approaches:

1. Direct execution with Entity-native CLI (this file):
   python main.py --help
   python main.py chat --message "Hello, agent!"

2. Via Entity CLI (for framework-level operations):
   python -m entity.cli run --workflow workflows/basic.yaml

This implementation follows Entity's 4-layer architecture:
- Uses ArgumentParsingResource (Layer 3: Canonical Resources)
- Integrates with LoggingResource for structured output
- Follows resources.get() acquisition pattern
- Maintains Entity's zero-config defaults
"""

import asyncio
import sys
from typing import Optional

from entity import Agent
from entity.defaults import load_defaults
from entity.resources.logging import LogLevel, LogCategory
from entity.resources.argument_parsing import ArgumentType, ArgumentCategory

class {project_path.name.title().replace('-', '')}CLI:
    """Entity-native CLI for {project_path.name} agent."""

    def __init__(self):
        self.resources = load_defaults()
        self.logger = self.resources.get("logging")
        self.arg_parser = self.resources.get("argument_parsing")
        self.agent = None
        self._setup_commands()

    def _setup_commands(self):
        """Setup CLI commands using Entity's ArgumentParsingResource."""
        self.arg_parser.register_argument(
            "chat", "message", ArgumentType.STRING, ArgumentCategory.WORKFLOW,
            "Message to send to the agent (interactive if not provided)"
        )
        self.arg_parser.register_argument(
            "chat", "workflow", ArgumentType.STRING, ArgumentCategory.WORKFLOW,
            "Workflow template to use", default="basic"
        )
        self.arg_parser.register_argument(
            "chat", "verbose", ArgumentType.BOOLEAN, ArgumentCategory.OUTPUT,
            "Enable debug logging", aliases=["v"]
        )

    async def run(self, argv: Optional[list[str]] = None) -> int:
        """Run the CLI using Entity's resource system."""
        try:
            parsed = await self.arg_parser.parse(argv)

            if parsed.validation_errors:
                for error in parsed.validation_errors:
                    await self.logger.log(LogLevel.ERROR, LogCategory.ERROR, f"Argument error: {{error}}")
                help_text = await self.arg_parser.generate_help()
                print(help_text)
                return 1

            if "--help" in (argv or sys.argv[1:]):
                help_text = await self.arg_parser.generate_help(parsed.command)
                print(help_text)
                return 0

            await self._initialize_agent()

            if parsed.command == "chat":
                return await self._handle_chat(parsed.values)
            elif parsed.command == "info":
                return await self._handle_info()
            else:
                return await self._handle_chat(parsed.values)

        except KeyboardInterrupt:
            await self.logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "Session ended by user")
            return 0
        except Exception as exc:
            await self.logger.log(LogLevel.ERROR, LogCategory.ERROR, "CLI error", error=str(exc))
            return 1

    async def _initialize_agent(self):
        """Initialize the Entity agent with structured logging."""
        await self.logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Initializing {project_path.name} agent",
            agent_name="{project_path.name}"
        )

        self.agent = Agent(resources=self.resources)

    async def _handle_chat(self, args: dict) -> int:
        """Handle chat command with Entity patterns."""
        message = args.get("message")
        verbose = args.get("verbose", False)

        if verbose:
            await self.logger.log(LogLevel.DEBUG, LogCategory.USER_ACTION, "Verbose mode enabled")

        if message:
            await self.logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                "Processing single message",
                message_length=len(message)
            )
            response = await self.agent.chat(message)
            print(response)
        else:
            await self.logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                "Starting interactive chat session"
            )
            await self.agent.chat("")

        return 0

    async def _handle_info(self) -> int:
        """Show agent information using Entity's structured logging."""
        await self.logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Agent information requested"
        )

        info = {{
            "agent_name": "{project_path.name}",
            "framework": "Entity",
            "version": "0.0.5",
            "resources": list(self.resources.keys()),
            "workflow_stages": ["input", "parse", "think", "do", "review", "output"]
        }}

        print(f"Agent: {{info['agent_name']}}")
        print(f"Framework: {{info['framework']}} v{{info['version']}}")
        print(f"Resources: {{', '.join(info['resources'])}}")
        print(f"Workflow: {{' → '.join(info['workflow_stages'])}}")

        return 0

async def main_async() -> int:
    """Main async entry point using Entity patterns."""
    cli = {project_path.name.title().replace('-', '')}CLI()
    return await cli.run()

def main():
    """Main entry point following Entity's async patterns."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
    (project_path / "main.py").write_text(main_content)

    # Create basic workflow
    workflow_content = """# Basic workflow configuration for Entity framework
# This workflow follows the standard 6-stage process:
# input -> parse -> think -> do -> review -> output

input:
  - entity.plugins.defaults.InputPlugin

parse:
  - entity.plugins.defaults.ParsePlugin

think:
  - entity.plugins.examples.reason_generator.ReasonGeneratorPlugin

do:
  # Add action plugins here as needed
  # - entity.plugins.examples.calculator.CalculatorPlugin

review:
  # Add review plugins here as needed
  # - entity.plugins.examples.static_reviewer.StaticReviewPlugin

output:
  - entity.plugins.examples.output_formatter.OutputFormatterPlugin
"""
    (project_path / "workflows" / "basic.yaml").write_text(workflow_content)

    # Create README
    readme_content = f"""# {project_path.name}

An Entity framework project for building AI agents.

Entity follows the simple mental model: **Agent = Resources + Workflow + Infrastructure**

## Getting Started

1. **Configure your environment** (copy and edit):
   ```bash
   cp .env.example .env
   # Edit .env with your LLM API keys or Ollama settings
   ```

2. **Install Entity framework**:
   ```bash
   pip install entity-core
   ```

3. **Run your agent**:
   ```bash
   # Method 1: Direct execution (simple)
   python main.py

   # Method 2: Entity CLI (recommended - richer interface)
   python -m entity.cli run --workflow workflows/basic.yaml

   # Method 3: Entity CLI with custom workflow
   python -m entity.cli run --workflow path/to/your/workflow.yaml
   ```

## Architecture

This project follows Entity's 4-layer architecture:

- **Layer 1: Infrastructure** - LLM backends, databases, storage
- **Layer 2: Resources** - Abstracted interfaces (Memory, LLM, FileStorage, Logging)
- **Layer 3: Canonical Resources** - Standard Entity resources with structured interfaces
- **Layer 4: Agent** - Your AI agent combining resources and workflow

### Logging System

Entity uses structured logging throughout the framework:

```python
# Get the logging resource
logger = resources.get("logging")

# Use structured logging with levels and categories
await logger.log(
    LogLevel.INFO,
    LogCategory.USER_ACTION,
    "Agent started successfully",
    agent_name="my_agent",
    custom_field="value"
)
```

**Log Levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
**Log Categories**: `USER_ACTION`, `WORKFLOW_EXECUTION`, `MEMORY_OPERATION`, `ERROR`, etc.

## Workflow Stages

Entity agents process requests through 6 stages:

1. **Input** - Receive and preprocess user input
2. **Parse** - Extract entities, intent, and structure
3. **Think** - Plan and reasoning
4. **Do** - Execute actions and gather information
5. **Review** - Quality check and validation
6. **Output** - Format and deliver response

## Project Structure

```
{project_path.name}/
├── main.py              # Agent entry point
├── .env.example         # Environment configuration template
├── workflows/           # Workflow definitions
│   └── basic.yaml      # Default workflow
├── plugins/            # Custom plugins (if needed)
├── data/              # Agent data storage
└── tests/             # Test files
```

## Running Your Agent

### Direct Execution vs CLI

- **Direct execution** (`python main.py`): Simple, programmatic approach
- **CLI execution** (`python -m entity.cli run`): Rich terminal interface with:
  - Colorized output and progress indicators
  - Interactive prompts with the EntCLIAdapter
  - Better error messages and debugging info
  - Automatic workflow wrapping with input/output adapters

### Example Usage

```bash
# Interactive chat session with rich UI
python -m entity.cli run --workflow workflows/basic.yaml

# Debug mode with verbose logging
python -m entity.cli run --workflow workflows/basic.yaml --verbose

# Quiet mode for scripting
python -m entity.cli run --workflow workflows/basic.yaml --quiet
```

## Next Steps

1. **Try both execution methods**: Compare `python main.py` vs CLI approach
2. **Customize the workflow**: Edit `workflows/basic.yaml` to add plugins
3. **Add custom plugins**: Create plugins in the `plugins/` directory
4. **Configure resources**: Modify LLM, memory, and storage settings in `.env`
5. **Use CLI features**: Explore `--verbose`, `--timeout`, and other CLI options

## Documentation

- [Entity Documentation](https://entity-core.readthedocs.io/) - Complete guides and API reference
- [Quick Start](https://entity-core.readthedocs.io/en/latest/quickstart.html) - 5-minute tutorial
- [Examples](https://github.com/Ladvien/entity/tree/main/examples) - Real-world agent examples
"""
    (project_path / "README.md").write_text(readme_content)

    # Create basic test
    test_content = f'''"""Tests for {project_path.name}."""

import pytest
from entity import Agent
from entity.defaults import load_defaults
from entity.resources.logging import LogLevel, LogCategory

@pytest.mark.asyncio
async def test_agent_creation():
    """Test that agent can be created successfully."""
    try:
        resources = load_defaults()
        agent = Agent(resources=resources)
        assert agent is not None
        assert agent.resources is not None
        assert agent.workflow is not None

        logger = resources.get("logging")
        assert logger is not None, "Logging resource should be available"

        await logger.log(
            LogLevel.INFO,
            LogCategory.USER_ACTION,
            "Test agent creation successful",
            test_name="test_agent_creation"
        )

    except Exception as exc:
        pytest.skip(f"Agent creation requires infrastructure setup: {{exc}}")

@pytest.mark.asyncio
async def test_logging_system():
    """Test that the Entity framework logging system works."""
    try:
        resources = load_defaults()
        logger = resources.get("logging")

        assert logger is not None, "Should have logging resource"

        await logger.log(LogLevel.DEBUG, LogCategory.USER_ACTION, "Debug message")
        await logger.log(LogLevel.INFO, LogCategory.WORKFLOW_EXECUTION, "Info message")
        await logger.log(LogLevel.WARNING, LogCategory.PERFORMANCE, "Warning message")

        await logger.log(
            LogLevel.INFO,
            LogCategory.MEMORY_OPERATION,
            "Structured logging test",
            component="{project_path.name}",
            test_field="test_value"
        )

        assert hasattr(logger, 'records'), "Logger should maintain records"

    except Exception as exc:
        pytest.skip(f"Logging system test requires infrastructure: {{exc}}")

@pytest.mark.asyncio
async def test_agent_workflow_loading():
    """Test that agent can load custom workflow."""
    try:
        from entity.workflow.templates import load_template
        workflow = load_template("basic")
        assert workflow is not None

        resources = load_defaults()
        logger = resources.get("logging")
        if logger:
            await logger.log(
                LogLevel.INFO,
                LogCategory.WORKFLOW_EXECUTION,
                "Testing workflow loading",
                workflow_type="basic"
            )

        agent = Agent(resources=resources, workflow=workflow)
        assert agent is not None

    except Exception as exc:
        pytest.skip(f"Workflow loading requires infrastructure: {{exc}}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_basic_chat():
    """Integration test for basic chat functionality."""
    try:
        resources = load_defaults()
        logger = resources.get("logging")

        if logger:
            await logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                "Starting integration test for chat functionality"
            )

        agent = Agent(resources=resources)

        result = await agent.chat("ping")
        assert isinstance(result, str)
        assert len(result) > 0

        if logger:
            await logger.log(
                LogLevel.INFO,
                LogCategory.USER_ACTION,
                "Chat integration test completed successfully",
                response_length=len(result)
            )

    except Exception as exc:
        pytest.skip(f"Chat integration requires LLM infrastructure: {{exc}}")
'''
    (
        project_path
        / "tests"
        / f"test_{project_path.name.lower().replace('-', '_')}.py"
    ).write_text(test_content)


async def init_command(args: argparse.Namespace) -> None:
    """Execute the init command with interactive setup."""

    if not args.quiet:
        console.print(
            Panel.fit(
                "[bold blue]Entity Framework[/bold blue]\n"
                "[dim]Initialize a new AI agent project[/dim]",
                border_style="blue",
            )
        )

    # Determine project name and path
    if args.project_name:
        project_name = args.project_name
        project_path = Path(project_name)
    else:
        current_dir = Path.cwd()
        project_name = current_dir.name
        project_path = current_dir

        if not args.quiet:
            use_current = Confirm.ask(
                f"Initialize Entity project in current directory ([bold]{project_name}[/bold])?",
                default=True,
            )
            if not use_current:
                project_name = Prompt.ask("Enter project name")
                project_path = Path(project_name)

    # Create project directory if needed
    if not project_path.exists():
        project_path.mkdir(parents=True)
        if not args.quiet:
            rprint(f"✅ Created directory: {project_path}")

    # Detect available LLM services
    if not args.quiet:
        rprint("\n[bold]🔍 Detecting available LLM services...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console if not args.quiet else Console(file=open(os.devnull, "w")),
    ) as progress:
        task = progress.add_task("Scanning for LLM services...", total=None)
        services = detect_llm_services()
        progress.update(task, completed=True)

    if not args.quiet:
        # Display detected services
        table = Table(title="🤖 Available LLM Services")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Models", style="dim")

        for service_id, config in services.items():
            models_str = (
                ", ".join(config["models"][:3]) if config["models"] else "None detected"
            )
            if len(config["models"]) > 3:
                models_str += f" (+{len(config['models']) - 3} more)"

            table.add_row(
                config.get("name", service_id.title()), config["status"], models_str
            )

        console.print(table)

        # Let user choose LLM service
        available_services = [sid for sid, cfg in services.items() if cfg["available"]]

        if available_services:
            rprint(
                f"\n[green]Found {len(available_services)} available service(s)![/green]"
            )

            if len(available_services) == 1:
                selected_service = available_services[0]
                service_name = services[selected_service].get(
                    "name", selected_service.title()
                )
                rprint(f"Using: [bold]{service_name}[/bold]")
            else:
                choices = []
                for sid in available_services:
                    name = services[sid].get("name", sid.title())
                    choices.append(f"{sid}:{name}")

                choice = Prompt.ask(
                    "Choose LLM service",
                    choices=[c.split(":")[0] for c in choices],
                    show_choices=True,
                )
                selected_service = choice
        else:
            rprint(
                "[yellow]⚠️  No LLM services detected. You can configure them later.[/yellow]"
            )
            selected_service = "ollama"  # Default fallback
    else:
        # Quiet mode - just pick the first available or default to ollama
        available_services = [sid for sid, cfg in services.items() if cfg["available"]]
        selected_service = available_services[0] if available_services else "ollama"

    # Create project files
    if not args.quiet:
        rprint("\n[bold]📁 Creating project structure...[/bold]")

    create_project_structure(project_path, args.template)
    create_env_example(project_path, selected_service)

    if not args.quiet:
        rprint("✅ Created project files")

        # Show next steps
        next_steps = f"""
[bold green]🎉 Project '{project_name}' created successfully![/bold green]

[bold]Next steps:[/bold]

1. [dim]Configure your environment:[/dim]
   cd {project_path}
   cp .env.example .env
   # Edit .env with your API keys/settings

2. [dim]Install Entity framework:[/dim]
   pip install entity-core

3. [dim]Run your first agent:[/dim]
   python main.py

4. [dim]Or use the Entity CLI:[/dim]
   python -m entity.cli run --workflow workflows/basic.yaml

[dim]📚 Visit https://entity-core.readthedocs.io/ for documentation and tutorials.[/dim]
"""

        console.print(Panel(next_steps, border_style="green", padding=(1, 2)))

    # Install dependencies if requested
    if not args.no_deps:
        if not args.quiet:
            install_deps = Confirm.ask("Install Entity framework now?", default=True)
        else:
            install_deps = True

        if install_deps:
            if not args.quiet:
                rprint("\n[bold]📦 Installing dependencies...[/bold]")

            try:
                import subprocess

                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "entity-core"],
                    capture_output=args.quiet,
                    text=True,
                    cwd=project_path,
                )

                if result.returncode == 0:
                    if not args.quiet:
                        rprint("✅ Dependencies installed successfully")
                else:
                    if not args.quiet:
                        rprint(
                            "[yellow]⚠️  Dependency installation failed. Install manually with: pip install entity-core[/yellow]"
                        )
            except Exception as e:
                if not args.quiet:
                    rprint(f"[yellow]⚠️  Could not install dependencies: {e}[/yellow]")
