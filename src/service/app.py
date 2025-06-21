import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM

from src.memory.vector_memory_system import VectorMemorySystem
from src.service.config import load_config
from src.service.agent import EntityAgent
from src.service.routes import EntityRouterFactory
from src.chat_storage import create_storage
from src.tools.tools import ToolManager
from src.adapters import create_output_adapters
from src.db.connection import initialize_global_db_connection
from src.core.registry import ServiceRegistry


logger = logging.getLogger(__name__)


def setup_logging(config):
    """Configure global logging with rotation and console output"""
    log_level = getattr(logging, config.logging.level.upper())
    formatter = logging.Formatter(config.logging.format)
    handlers = [logging.StreamHandler()]

    if config.logging.file_enabled:
        Path(config.logging.file_path).parent.mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler

        handlers.append(
            RotatingFileHandler(
                filename=config.logging.file_path,
                maxBytes=config.logging.max_file_size,
                backupCount=config.logging.backup_count,
            )
        )

    for handler in handlers:
        handler.setLevel(log_level)
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        format=config.logging.format,
        handlers=handlers,
        force=True,
    )

    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger.info(f"✅ Logging configured - Level: {config.logging.level}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Entity Agent Service")

    try:
        # Load config
        config = load_config("config.yaml")
        setup_logging(config)
        ServiceRegistry.register("config", config)

        # Init DB
        db_connection = await initialize_global_db_connection(config.database)
        ServiceRegistry.register("db_connection", db_connection)

        # Init chat storage
        storage = await create_storage(config.storage, config.database)
        ServiceRegistry.register("storage", storage)

        # Init vector memory 🧠
        try:
            memory_system = VectorMemorySystem(
                config.memory, config.database
            )  # noqa: F821
            await memory_system.initialize()
            ServiceRegistry.register("memory_system", memory_system)
            logger.info("✅ Vector memory system registered")
        except Exception as e:
            logger.warning(f"⚠️ Skipping vector memory init: {e}")

        # Init tool manager 🔧
        tool_manager = ToolManager.setup(
            plugin_directory=config.tools.plugin_path,
            enabled_tools=config.tools.enabled,
        )
        ServiceRegistry.register("tool_manager", tool_manager)

        # Init output adapters
        output_adapters = create_output_adapters(config)
        ServiceRegistry.register("output_adapter_manager", output_adapters)

        if output_adapters.adapters:
            await test_output_adapters_simple(output_adapters)

        # Init LLM
        llm = OllamaLLM(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            top_p=config.ollama.top_p,
            top_k=config.ollama.top_k,
            repeat_penalty=config.ollama.repeat_penalty,
        )
        ServiceRegistry.register("llm", llm)

        # Init Agent
        agent = EntityAgent(
            config=config.entity,
            tool_manager=tool_manager,
            chat_storage=storage,
            llm=llm,
            output_adapter_manager=output_adapters,
        )
        await agent.initialize()
        ServiceRegistry.register("agent", agent)

        # Attach to app
        app.state.registry = ServiceRegistry
        app.state.agent = agent

        # Attach routes
        router = EntityRouterFactory(agent, tool_manager, storage).get_router()
        app.include_router(router, prefix="/api/v1")

        # Log success
        ServiceRegistry.mark_initialized()
        logger.info("✅ Entity Agent ready with services:")
        for name, svc in ServiceRegistry.list_services().items():
            logger.info(f"  - {name}: {svc.__class__.__name__}")

        yield

    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}", exc_info=True)
        raise

    finally:
        logger.info("👋 Shutting down Entity Agent Service")
        await ServiceRegistry.shutdown()


async def test_output_adapters_simple(manager):
    """Test all output adapters with `test_connection()` support."""
    for adapter in getattr(manager, "adapters", []):
        if hasattr(adapter, "test_connection"):
            name = adapter.__class__.__name__
            try:
                result = await adapter.test_connection()
                status = "✅" if result else "⚠️"
                logger.info(f"{status} {name} connection test")
            except Exception as e:
                logger.warning(f"❌ {name} test failed: {e}")


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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
