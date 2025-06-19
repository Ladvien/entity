# entity_service/main.py
"""
Entity Agent FastAPI Service with PostgreSQL Memory - Main entry point
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.old.memory import VectorMemorySystem
from src.service.config import load_config
from src.service.agent import EntityAgent


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting Entity Agent Service with PostgreSQL Memory")

    # Load configuration
    config = load_config("config/agent_config.yaml")

    # Initialize vector memory system
    memory_system = VectorMemorySystem(
        memory_config=config.memory, database_config=config.database
    )
    await memory_system.initialize()
    logger.info("✅ Vector memory system initialized")

    # Initialize chat history storage (separate from vector memory)
    storage = create_storage(config.storage)

    # Setup tools with memory context
    tool_registry = await setup_tools(config.tools, memory_system)

    # Create agent
    agent = EntityAgent(
        config=config.agent,
        tool_registry=tool_registry,
        storage=storage,
        memory_system=memory_system,
    )
    await agent.initialize()

    # Store in app state
    app.state.config = config
    app.state.agent = agent
    app.state.storage = storage
    app.state.memory_system = memory_system
    app.state.tool_registry = tool_registry

    logger.info("✅ Entity Agent Service started successfully")

    yield

    # Shutdown
    logger.info("👋 Shutting down Entity Agent Service")
    await agent.cleanup()
    await memory_system.close()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Entity Agent Service",
        version="2.0.0",
        description="Entity Agent with PostgreSQL Vector Memory",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup routes
    app.include_router(create_routes(), prefix="/api/v1")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
