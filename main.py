# main.py - Clean entry point with proper separation of concerns

import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from src.config import ConfigLoader
from src.application_layer import ApplicationService, create_application_service
from src.routes import APIRoutes
from src.chat_cli import ChatCLI
from src.application_layer import EntitySystemError


# Global application service for FastAPI lifespan
app_service: ApplicationService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    global app_service

    try:
        config = ConfigLoader().load()
        app_service = ApplicationService(config)
        await app_service.initialize()
        yield
    finally:
        if app_service:
            await app_service.cleanup()


def create_fastapi_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = ConfigLoader().load()

    app = FastAPI(
        title="Entity Agentic System with Vector Memory",
        description=f"Jade the Demoness - An AI entity with {config.entity.name}",
        version="2.0.0",
        debug=config.debug,
        lifespan=lifespan,
    )

    # Register routes after app_service is available
    @app.on_event("startup")
    async def setup_routes():
        if app_service:
            api_routes = APIRoutes(app_service)
            api_routes.register_routes(app)

    return app


async def run_chat_mode():
    """Run interactive chat mode."""
    config = ConfigLoader().load()

    async with create_application_service(config) as app_service:
        chat_cli = ChatCLI(app_service)
        await chat_cli.start()


def run_server_mode():
    """Run FastAPI server mode."""
    config = ConfigLoader().load()

    app = create_fastapi_app()

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level,
    )


def run_simple_test():
    """Run simple test mode for debugging."""
    config = ConfigLoader().load()

    print("🧪 Simple test mode...")
    print("Testing basic imports...")

    try:
        from src.agent import EntityAgent

        print("✅ EntityAgent import successful")

        agent = EntityAgent(config=config)
        print("✅ EntityAgent creation successful")
        print(f"   Entity: {config.entity.name}")
        print(f"   Model: {config.ollama.model}")
        print(f"   Debug: {config.debug}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


def show_config():
    """Show current configuration."""
    config = ConfigLoader().load()

    sections = [
        (
            "ENTITY CONFIGURATION",
            {
                "Entity ID": config.entity.entity_id,
                "Entity Name": config.entity.name,
                "Sarcasm Level": config.entity.sarcasm_level,
                "Loyalty Level": config.entity.loyalty_level,
                "Anger Level": config.entity.anger_level,
                "Wit Level": config.entity.wit_level,
                "Response Brevity": config.entity.response_brevity,
                "Memory Influence": config.entity.memory_influence,
            },
        ),
        (
            "OLLAMA CONFIGURATION",
            {
                "Base URL": config.ollama.base_url,
                "Model": config.ollama.model,
                "Temperature": config.ollama.temperature,
                "Top P": config.ollama.top_p,
                "Top K": config.ollama.top_k,
                "Repeat Penalty": config.ollama.repeat_penalty,
            },
        ),
        (
            "DATABASE CONFIGURATION",
            {
                "Host": config.database.host,
                "Port": config.database.port,
                "Database": config.database.name,
                "Username": config.database.username,
                "Connection String": config.database.connection_string.replace(
                    config.database.password, "***"
                ),
            },
        ),
        (
            "SERVER CONFIGURATION",
            {
                "Host": config.server.host,
                "Port": config.server.port,
                "Reload": config.server.reload,
                "Log Level": config.server.log_level,
            },
        ),
    ]

    for title, data in sections:
        print(f"\n{'=' * 50}")
        print(title)
        print("=" * 50)
        for key, value in data.items():
            print(f"{key}: {value}")

    print(f"\n{'=' * 50}")
    print(f"Debug Mode: {config.debug}")


def setup_logging():
    """Setup logging configuration."""
    try:
        config = ConfigLoader().load()
        logging.basicConfig(
            level=getattr(logging, config.logging.level.upper()),
            format=config.logging.format,
        )
    except Exception as e:
        # Fallback logging if config fails
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to load logging config: {e}")


def main():
    """Main entry point with command dispatch."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "server"

    try:
        if mode == "chat":
            logger.info("🚀 Starting chat-only mode...")
            asyncio.run(run_chat_mode())

        elif mode == "server":
            logger.info("🚀 Starting FastAPI server...")
            run_server_mode()

        elif mode == "simple":
            run_simple_test()

        elif mode == "config":
            show_config()

        else:
            logger.info("🚀 Starting FastAPI server (default)...")
            logger.info("💡 Available modes:")
            logger.info("   python main.py chat    - Chat-only mode")
            logger.info("   python main.py server  - Server only (default)")
            logger.info("   python main.py simple  - Simple test mode")
            logger.info("   python main.py config  - Show configuration")
            run_server_mode()

    except EntitySystemError as e:
        logger.error(f"Entity system error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
