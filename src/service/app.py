# src/service/main.py - FIXED VERSION

import logging
from contextlib import asynccontextmanager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with centralized database connection"""
    logger.info("🚀 Starting Entity Agent Service with PostgreSQL Memory")

    # Load YAML configuration
    config = load_config("config.yaml")

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

    # Setup tool registry - FIXED: Complete the line
    tool_registry = ToolManager.setup(config.tools.plugin_path)
    logger.info(
        f"✅ Tool registry initialized with {len(tool_registry.list_tool_names())} tools"
    )

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
