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
import click

# Import your existing modules
from src.service.config import load_config
from src.cli.client import EntityAPIClient
from src.cli.chat_interface import ChatInterface

console = Console()


@click.group(invoke_without_command=True)
@click.option("--config", "-c", default="config.yaml", help="Configuration file path")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, config, debug):
    """Entity AI Agent - Your personal AI assistant with memory"""

    if debug:
        logging.basicConfig(level=logging.DEBUG)

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
            log_level=config.server.log_level.lower(),
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
