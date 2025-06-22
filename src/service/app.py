import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from langchain_ollama import OllamaLLM
from src.service.config import load_config
from src.db.connection import (
    close_global_db_connection,
    initialize_global_db_connection,
)
from src.memory.memory_system import MemorySystem
from src.service.agent import EntityAgent
from src.service.routes import EntityRouterFactory
from src.adapters import create_output_adapters
from src.tools.tools import ToolManager
from src.core.registry import ServiceRegistry


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


# src/service/app.py - FIXED LIFESPAN


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    setup_logging(config)
    ServiceRegistry.register("config", config)

    db = await initialize_global_db_connection(config.database)
    ServiceRegistry.register("db", db)

    memory_system = MemorySystem(
        memory_config=config.memory,
        database_config=config.database,
        storage_config=config.storage,
    )
    await memory_system.initialize()
    ServiceRegistry.register("memory", memory_system)

    tool_manager = ToolManager()
    tool_manager.load_plugins_from_config("plugins")
    ServiceRegistry.register("tools", tool_manager)

    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
        base_template=config.entity.prompts.base_prompt.strip(),
    )

    agent = EntityAgent(
        config=config.entity,
        tool_manager=tool_manager,
        llm=llm,
        memory_system=memory_system,
        output_adapter_manager=create_output_adapters(config),
    )

    # ✅ CRITICAL: Initialize the agent!
    await agent.initialize()

    ServiceRegistry.register("agent", agent)

    # ✅ Register routes here via the app instance
    router = EntityRouterFactory(agent, tool_manager, memory_system).get_router()
    app.include_router(router, prefix="/api/v1")

    yield  # App is now live

    await close_global_db_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Entity Agent Service",
        version="2.0.0",
        description="LLM-powered character agent framework",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def register_routes():
        agent = ServiceRegistry.get("agent")
        tools = ServiceRegistry.get("tools")
        memory = ServiceRegistry.get("memory")

        router = EntityRouterFactory(agent, tools, memory).get_router()
        app.include_router(router, prefix="/api/v1")  # 🔥 this is what’s missing

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, loop="uvloop")
