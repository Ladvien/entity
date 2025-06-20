# src/service/main.py - Quick fix to use existing approach

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
from src.tools.tools import setup_tools

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🚀 Starting Entity Agent Service with PostgreSQL Memory")

    # Load YAML configuration
    config = load_config("config.yaml")

    # Initialize memory system
    memory_system = VectorMemorySystem(
        memory_config=config.memory, database_config=config.database
    )
    await memory_system.initialize()
    logger.info("✅ Vector memory system initialized")

    # Initialize chat history storage
    storage = await create_storage(config.storage, config.database)
    logger.info("✅ Chat storage initialized")

    # Setup tool registry
    tool_registry = await setup_tools(config.tools, memory_system)

    # Initialize LLM
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
    )

    # Initialize agent
    agent = EntityAgent(
        config=config.entity,
        tool_registry=tool_registry,
        chat_storage=storage,
        memory_system=memory_system,
        llm=llm,
    )
    await agent.initialize()

    # Attach everything to app.state
    app.state.config = config
    app.state.agent = agent
    app.state.storage = storage
    app.state.memory_system = memory_system
    app.state.tool_registry = tool_registry

    # Attach dynamic router
    router_factory = EntityRouterFactory(agent, memory_system, tool_registry, storage)
    app.include_router(router_factory.get_router(), prefix="/api/v1")

    logger.info("✅ Entity Agent Service started successfully")
    yield

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
