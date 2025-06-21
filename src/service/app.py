# src/service/app.py - FIXED VERSION

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM

from src.service.agent import EntityAgent
from src.service.config import load_config
from src.service.routes import EntityRouterFactory
from src.storage import create_storage
from src.tools.memory import VectorMemorySystem
from src.tools.tools import ToolManager
from src.db.connection import DatabaseConnection, initialize_global_db_connection

logger = logging.getLogger(__name__)


def setup_logging(config):
    """Setup comprehensive logging configuration"""
    # Create logs directory if needed
    if config.logging.file_enabled:
        log_path = Path(config.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    log_level = getattr(logging, config.logging.level.upper())

    # Create formatters
    formatter = logging.Formatter(config.logging.format)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Setup file handler if enabled
    handlers = [console_handler]
    if config.logging.file_enabled:
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            config.logging.file_path,
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level, format=config.logging.format, handlers=handlers, force=True
    )

    # Set specific logger levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logger.info(
        f"✅ Logging configured - Level: {config.logging.level}, File: {config.logging.file_enabled}"
    )


def inject_memory_into_tools_simple(
    tool_manager: ToolManager, memory_system: VectorMemorySystem
):
    """Simple and reliable memory injection"""
    try:
        # Store memory system globally so tools can access it
        import src.tools.tools as tools_module

        tools_module._global_memory_system = memory_system
        logger.info(f"✅ Memory system stored globally for tool access")

        # Also try direct injection for better reliability
        for tool in tool_manager.get_all_tools():
            if tool.name in ["memory_search", "store_memory"]:
                try:
                    # Create a direct reference
                    setattr(tool, "_memory_system", memory_system)
                    logger.info(
                        f"✅ Memory system directly injected into {tool.name} tool"
                    )
                except Exception as e:
                    logger.debug(f"Direct injection failed for {tool.name}: {e}")

    except Exception as e:
        logger.warning(f"⚠️ Memory injection failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with centralized database connection"""
    logger.info("🚀 Starting Entity Agent Service with PostgreSQL Memory")

    # Load YAML configuration
    config = load_config("config.yaml")

    # Setup logging
    setup_logging(config)

    # Initialize centralized database connection
    logger.info("🔗 Setting up centralized database connection...")
    db_connection = await initialize_global_db_connection(config.database)
    logger.info(f"✅ Global database connection established: {db_connection}")

    # Initialize memory system with centralized connection
    memory_system = VectorMemorySystem(
        memory_config=config.memory, database_config=config.database
    )
    await memory_system.initialize()
    logger.info("✅ Vector memory system initialized with centralized connection")

    # Initialize chat history storage with centralized connection
    storage = await create_storage(config.storage, config.database)
    logger.info("✅ Chat storage initialized with centralized connection")

    # Setup tool registry - FIXED: Complete the line and load tools properly
    logger.info(f"🔧 Loading tools from: {config.tools.plugin_path}")
    tool_registry = ToolManager.setup(
        plugin_directory=config.tools.plugin_path,
        enabled_tools=getattr(config.tools, "enabled", None),
    )
    logger.info(
        f"✅ Tool registry initialized with {len(tool_registry.list_tool_names())} tools: {tool_registry.list_tool_names()}"
    )

    # Inject memory system into memory tools
    inject_memory_into_tools_simple(tool_registry, memory_system)

    # Initialize LLM
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
    )
    logger.info(f"✅ LLM initialized: {config.ollama.model}")

    # Initialize agent
    agent = EntityAgent(
        config=config.entity,
        tool_manager=tool_registry,
        chat_storage=storage,
        memory_system=memory_system,
        llm=llm,
    )
    await agent.initialize()
    logger.info("✅ Entity agent initialized")

    # Attach everything to app.state
    app.state.config = config
    app.state.agent = agent
    app.state.storage = storage
    app.state.memory_system = memory_system
    app.state.tool_registry = tool_registry
    app.state.db_connection = db_connection  # Store reference to centralized connection

    # Attach dynamic router
    router_factory = EntityRouterFactory(agent, memory_system, tool_registry, storage)
    app.include_router(router_factory.get_router(), prefix="/api/v1")

    logger.info("✅ Entity Agent Service started successfully")
    logger.info(f"🛠️ Available tools: {tool_registry.list_tool_names()}")
    yield

    # Cleanup phase
    logger.info("👋 Shutting down Entity Agent Service")

    try:
        await agent.cleanup()
        await memory_system.close()
        await storage.close()
        await db_connection.close()
        logger.info("✅ All services shut down cleanly")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Entity Agent Service",
        version="2.0.0",
        description="Entity Agent with PostgreSQL Vector Memory",
        lifespan=lifespan,
    )

    # Add CORS
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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
