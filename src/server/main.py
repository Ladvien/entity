# src/server/main.py

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from langchain_ollama import OllamaLLM

from src.plugins.registry import ToolManager
from src.server.routes.agent import EntityAgent
from src.server.routes.routes import EntityRouterFactory
from src.core.config import load_config
from src.db.connection import (
    close_global_db_connection,
    initialize_global_db_connection,
)
from src.memory.memory_system import MemorySystem
from src.adapters import create_adapters
from src.core.registry import ServiceRegistry
from src.service.react_validator import ReActPromptValidator

logger = logging.getLogger(__name__)


def setup_logging(config):
    log_level = getattr(logging, config.logging.level.upper())
    formatter = logging.Formatter(config.logging.format)

    handlers = [logging.StreamHandler()]

    if config.logging.file_enabled:
        Path(config.logging.file_path).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=config.logging.file_path,
                maxBytes=config.logging.max_file_size,
                backupCount=config.logging.backup_count,
            )
        )

    for h in handlers:
        h.setLevel(log_level)
        h.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        format=config.logging.format,
        handlers=handlers,
        force=True,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger.info(f"✅ Logging configured - Level: {config.logging.level}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    setup_logging(config)
    ServiceRegistry.register("config", config)

    # Validate ReAct prompt on startup
    logger.info("🔍 Validating ReAct prompt configuration...")
    validation_passed = ReActPromptValidator.validate_on_startup(config.entity)

    if not validation_passed:
        logger.error("❌ ReAct prompt validation failed! Check the output above.")
        logger.error("💡 Server will continue but may experience parsing errors.")
        logger.error("🔧 Run 'entity validate_prompt' for detailed validation report.")
    else:
        logger.info("✅ ReAct prompt validation passed!")

    # Initialize database
    logger.info("🔗 Initializing global database connection...")
    logger.debug(f"Database config: {config.database}")
    db = await initialize_global_db_connection(config.database)
    ServiceRegistry.register("db", db)

    # Initialize memory system
    memory_system = MemorySystem(
        memory_config=config.memory,
        database_config=config.database,
    )
    await memory_system.initialize()
    ServiceRegistry.register("memory", memory_system)

    # Initialize tool manager
    tool_manager = ToolManager(config.tools)
    tool_manager.load_plugins_from_config(config.tools.plugin_path)

    for tool in tool_manager.get_all_tools():
        logger.info(f"✅ Registered tool: {tool.name}")

    ServiceRegistry.register("tools", tool_manager)

    # Initialize LLM
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
        base_template=config.entity.prompts.base_prompt.strip(),
    )

    # Initialize output adapters BEFORE creating the agent
    logger.info("🔌 Initializing output adapters...")
    output_adapter_manager = create_adapters(config)
    ServiceRegistry.register("output_adapters", output_adapter_manager)

    # Test TTS adapter connection if enabled
    if output_adapter_manager.adapters:
        for adapter in output_adapter_manager.adapters:
            if hasattr(adapter, "test_connection"):
                try:
                    logger.info(
                        f"🔍 Testing {adapter.__class__.__name__} connection..."
                    )
                    connection_ok = await adapter.test_connection()
                    if connection_ok:
                        logger.info(
                            f"✅ {adapter.__class__.__name__} connection successful"
                        )
                    else:
                        logger.warning(
                            f"⚠️ {adapter.__class__.__name__} connection failed"
                        )
                except Exception as e:
                    logger.warning(
                        f"⚠️ {adapter.__class__.__name__} connection test error: {e}"
                    )

    # Initialize agent with adapters
    agent = EntityAgent(
        config=config.entity,
        tool_manager=tool_manager,
        llm=llm,
        memory_system=memory_system,
        output_adapter_manager=output_adapter_manager,
    )

    # Initialize the agent
    await agent.initialize()

    ServiceRegistry.register("agent", agent)

    # Register routes here via the app instance
    router = EntityRouterFactory(agent, tool_manager, memory_system).get_router()
    app.include_router(router, prefix="/api/v1")

    # Mark registry as fully initialized
    ServiceRegistry.mark_initialized()

    logger.info("🚀 Entity Agent Service fully initialized and ready!")

    yield  # App is now live

    # Cleanup on shutdown
    logger.info("🛑 Shutting down Entity Agent Service...")

    # Close output adapters first
    if output_adapter_manager:
        await output_adapter_manager.close_all()

    # Close database connection
    await close_global_db_connection()

    # Shutdown service registry
    await ServiceRegistry.shutdown()

    logger.info("✅ Entity Agent Service shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Entity Agent Service",
        version="2.0.0",
        description="LLM-powered character agent framework with TTS support",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, loop="uvloop")
