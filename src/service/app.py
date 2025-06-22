import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from langchain_ollama import OllamaLLM
from src.service.config import load_config
from src.db.connection import initialize_global_db_connection
from src.memory.memory_system import MemorySystem
from src.service.agent import EntityAgent
from src.service.routes import EntityRouterFactory
from src.adapters import create_output_adapters
from src.tools.tools import ToolManager
from src.core.registry import ServiceRegistry
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from src.service.config import load_config
from src.memory.memory_system import MemorySystem
from src.db.connection import initialize_global_db_connection
from src.service.agent import EntityAgent
from src.tools.tools import ToolManager
from src.adapters import create_output_adapters
from src.core.registry import ServiceRegistry
from src.service.routes import EntityRouterFactory
from langchain_ollama import OllamaLLM


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
    logger.info("🚀 Starting Entity Agent Service")

    try:
        # 1. Load config
        config = load_config("config.yaml")
        ServiceRegistry.register("config", config)

        setup_logging(config)

        # 3. Init DB
        db_connection = await initialize_global_db_connection(config.database)
        ServiceRegistry.register("db_connection", db_connection)

        # 4. Init memory system fully inside loop
        memory_system = MemorySystem(config.memory, config.database, config.storage)
        await memory_system.initialize()
        ServiceRegistry.register("memory_system", memory_system)

        # 5. Init tool manager (sync, no `asyncio.run`)
        tool_manager = ToolManager.setup(
            plugin_directory=config.tools.plugin_path,
            enabled_tools=config.tools.enabled,
        )
        ServiceRegistry.register("tool_manager", tool_manager)

        # 6. Init output adapters (optional async test call stays inside loop)
        output_adapters = create_output_adapters(config)
        ServiceRegistry.register("output_adapter_manager", output_adapters)

        if output_adapters.adapters:
            for adapter in output_adapters.adapters:
                if hasattr(adapter, "test_connection"):
                    await adapter.test_connection()

        # 7. Init LLM
        llm = OllamaLLM(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            top_p=config.ollama.top_p,
            top_k=config.ollama.top_k,
            repeat_penalty=config.ollama.repeat_penalty,
        )
        ServiceRegistry.register("llm", llm)

        # 8. Init agent
        agent = EntityAgent(
            config=config.entity,
            tool_manager=tool_manager,
            llm=llm,
            memory_system=memory_system,
            output_adapter_manager=output_adapters,
        )
        await agent.initialize()
        ServiceRegistry.register("agent", agent)

        # 9. Add to app
        app.state.registry = ServiceRegistry
        app.state.agent = agent

        # 10. Attach routes
        router = EntityRouterFactory(agent, tool_manager, memory_system).get_router()
        app.include_router(router, prefix="/api/v1")

        ServiceRegistry.mark_initialized()
        logger.info("✅ Entity Agent ready")

        yield

    except Exception as e:
        logger.error(f"❌ Application failed: {e}", exc_info=True)
        raise

    finally:
        await ServiceRegistry.shutdown()
        logger.info("👋 Shutdown complete")


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

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, loop="uvloop")
