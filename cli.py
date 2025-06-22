#!/usr/bin/env python3
"""
Entity CLI - Single entry point
"""
import sys
import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import click

# Import your existing modules
from src.service.react_validator import ReActPromptValidator
from src.shared.agent_result import AgentResult
from src.service.config import load_config
from src.cli.client import EntityAPIClient
from src.cli.chat_interface import ChatInterface

# ✅ Import the proper render function
from src.cli.render import render_agent_result

console = Console()

# ✅ REMOVE the old render function from cli.py - use the one from src/cli/render.py


@click.group(invoke_without_command=True)
@click.option("--config", "-c", default="config.yml", help="Configuration file path")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, config, debug):
    """Entity AI Agent - Your personal AI assistant with memory"""

    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )

    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config

    if ctx.invoked_subcommand is None:
        welcome_text = """[bold cyan]🤖 Entity AI Agent[/bold cyan]
[dim]Your personal AI assistant with persistent memory[/dim]

[yellow]Quick Start:[/yellow]
- [bold]entity chat[/bold] - Start interactive chat
- [bold]entity server[/bold] - Run API server  
- [bold]entity status[/bold] - Check system status"""

        console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))
        console.print(ctx.get_help())


@cli.command()
@click.pass_context
def chat(ctx):
    """Start interactive chat with your AI agent"""
    asyncio.run(run_chat_mode(ctx.obj["config_path"]))


@cli.command()
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.pass_context
def server(ctx, reload):
    """Start the Entity API server"""
    run_server_mode(ctx.obj["config_path"], reload)


@cli.command()
@click.pass_context
def status(ctx):
    """Check system status and configuration"""
    asyncio.run(show_status(ctx.obj["config_path"]))


@cli.command()
@click.pass_context
def validate_prompt(ctx):
    """Validate ReAct prompt configuration"""
    from rich.table import Table
    from rich.panel import Panel

    try:
        config = load_config(ctx.obj["config_path"])

        console.print("[bold blue]🔍 ReAct Prompt Validation[/bold blue]\n")

        # Get validation report
        report = ReActPromptValidator.get_validation_report(config)
        is_valid = report["is_valid"]

        # Overall status
        status_color = "green" if is_valid else "red"
        status_text = "✅ VALID" if is_valid else "❌ INVALID"
        console.print(
            f"[bold {status_color}]Status: {status_text}[/bold {status_color}]\n"
        )

        # Required variables table
        req_table = Table(title="Required Variables", show_header=True)
        req_table.add_column("Variable", style="bold")
        req_table.add_column("Status", justify="center")

        for var in ReActPromptValidator.REQUIRED_VARIABLES:
            if var in report["required_variables"]["present"]:
                req_table.add_row(var, "[green]✅ Present[/green]")
            else:
                req_table.add_row(var, "[red]❌ Missing[/red]")

        console.print(req_table)
        console.print()

        # Template variables analysis
        if report["template_variables"]["undeclared"]:
            console.print(
                "[bold yellow]⚠️ Undeclared Variables in Template:[/bold yellow]"
            )
            for var in report["template_variables"]["undeclared"]:
                console.print(f"  • {var}")
            console.print()

        if report["template_variables"]["unused"]:
            console.print("[bold yellow]⚠️ Declared but Unused Variables:[/bold yellow]")
            for var in report["template_variables"]["unused"]:
                console.print(f"  • {var}")
            console.print()

        # ReAct patterns
        pattern_table = Table(title="ReAct Format Patterns", show_header=True)
        pattern_table.add_column("Pattern", style="bold")
        pattern_table.add_column("Status", justify="center")

        for pattern in ReActPromptValidator.REACT_PATTERNS:
            if pattern in report["react_patterns"]["found"]:
                pattern_table.add_row(pattern, "[green]✅ Found[/green]")
            else:
                pattern_table.add_row(pattern, "[yellow]⚠️ Missing[/yellow]")

        console.print(pattern_table)
        console.print()

        # Suggestions if invalid
        if not is_valid:
            suggestions = ReActPromptValidator.suggest_fixes(config)
            if suggestions:
                console.print("[bold red]💡 Suggested Fixes:[/bold red]")
                for i, suggestion in enumerate(suggestions, 1):
                    console.print(f"  {i}. {suggestion}")
                console.print()

        # Show current prompt snippet
        prompt_snippet = (
            config.prompts.base_prompt[:300] + "..."
            if len(config.prompts.base_prompt) > 300
            else config.prompts.base_prompt
        )
        console.print(
            Panel(
                prompt_snippet,
                title="Current Prompt Template (snippet)",
                border_style="dim",
            )
        )

    except Exception as e:
        console.print(f"❌ Validation failed: {e}", style="red")
        sys.exit(1)


# Implementation functions using your existing code
async def run_chat_mode(config_path: str):
    """Use your existing chat mode logic"""
    try:
        config = load_config(config_path)
        console.print(
            f"🔗 Connecting to Entity server at [cyan]{config.server.host}:{config.server.port}[/cyan]"
        )

        client = EntityAPIClient(f"http://{config.server.host}:{config.server.port}")

        # Quick health check
        try:
            health = await client.health_check()
            if health.get("status") != "healthy":
                console.print(
                    "⚠️  Server appears to be down. Start it with: [bold]entity server[/bold]",
                    style="yellow",
                )
        except:
            console.print(
                "⚠️  Can't reach server. Start it with: [bold]entity server[/bold]",
                style="yellow",
            )

        interface = ChatInterface(client, config={"save_locally": True})
        await interface.run()

    except Exception as e:
        console.print(f"❌ Chat failed: {e}", style="red")
        sys.exit(1)


def run_server_mode(config_path: str, reload: bool = False):
    """Use your existing server mode logic"""
    try:
        config = load_config(config_path)

        if reload:
            config.server.reload = True

        console.print(
            f"🚀 Starting Entity server on [cyan]{config.server.host}:{config.server.port}[/cyan]"
        )

        # Fix the import - use the correct path
        import uvicorn
        from src.service.app import create_app

        app = create_app()
        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.port,
            reload=config.server.reload,
            log_level=config.server.log_level.lower(),  # from config.yml
            access_log=True,
        )

    except Exception as e:
        console.print(f"❌ Server failed: {e}", style="red")
        sys.exit(1)


async def show_status(config_path: str):
    """Show system status"""
    try:
        config = load_config(config_path)

        console.print("\n[bold]📊 Entity System Status[/bold]")

        status_table = Table(show_header=False)
        status_table.add_column("Component", style="bold")
        status_table.add_column("Status")

        status_table.add_row("⚙️  Configuration", "[green]✓ Loaded[/green]")
        status_table.add_row(
            "🤖 Agent", f"[green]✓ {config.entity.personality.name}[/green]"
        )
        status_table.add_row("🧠 Model", f"[green]✓ {config.ollama.model}[/green]")

        # Check if server is running
        try:
            client = EntityAPIClient(
                f"http://{config.server.host}:{config.server.port}"
            )
            health = await client.health_check()
            if health.get("status") == "healthy":
                status_table.add_row("🌐 Server", "[green]✓ Running[/green]")
            else:
                status_table.add_row("🌐 Server", "[red]✗ Down[/red]")
        except:
            status_table.add_row("🌐 Server", "[red]✗ Down[/red]")

        console.print(status_table)

        console.print(
            f"\n🛠️  [bold]Enabled Tools:[/bold] {', '.join(config.tools.enabled)}"
        )
        console.print(f"\n💡 [bold]Quick Commands:[/bold]")
        console.print("   • [cyan]entity chat[/cyan] - Start chatting")
        console.print("   • [cyan]entity server[/cyan] - Start API server")

    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")


if __name__ == "__main__":
    cli()
