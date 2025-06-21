# src/service/app.py - UPDATED WITH SERVICEREGISTRY

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
from src.adapters import create_output_adapters
from src.core.registry import ServiceRegistry  # NEW IMPORT

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


# NO MORE COMPLEX INJECTION FUNCTIONS!
# The entire inject_memory_into_tools_comprehensive function is DELETED!
# The entire verify_memory_injection function is DELETED!
# The entire test_output_adapters function is simplified!


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simplified application lifecycle with ServiceRegistry - NO MORE INJECTION HACKS!"""
    logger.info("🚀 Starting Entity Agent Service with ServiceRegistry")

    try:
        # 1. Load and register configuration
        config = load_config("config.yaml")
        setup_logging(config)
        ServiceRegistry.register("config", config)
        logger.info("✅ Configuration loaded and registered")

        # 2. Initialize and register database connection
        logger.info("🔗 Setting up database connection...")
        db_connection = await initialize_global_db_connection(config.database)
        ServiceRegistry.register("db_connection", db_connection)
        logger.info(f"✅ Database connection registered: {db_connection}")

        # 3. Initialize and register memory system
        logger.info("🧠 Initializing memory system...")
        memory_system = VectorMemorySystem(
            memory_config=config.memory, database_config=config.database
        )
        await memory_system.initialize()
        ServiceRegistry.register("memory_system", memory_system)
        logger.info("✅ Memory system registered")

        # 4. Initialize and register storage
        logger.info("💾 Setting up storage...")
        storage = await create_storage(config.storage, config.database)
        ServiceRegistry.register("storage", storage)
        logger.info("✅ Storage registered")

        # 5. Setup and register tool manager
        logger.info("🔧 Loading tools...")
        tool_registry = ToolManager.setup(
            plugin_directory=config.tools.plugin_path,
            enabled_tools=getattr(config.tools, "enabled", None),
        )
        ServiceRegistry.register("tool_manager", tool_registry)
        logger.info(
            f"✅ Tool manager registered with {len(tool_registry.list_tool_names())} tools"
        )

        # 6. NO MORE MEMORY INJECTION HACK!
        # Tools automatically get memory system via ServiceRegistry!
        logger.info("🎉 No memory injection needed - tools use ServiceRegistry!")

        # 7. Initialize and register output adapters
        logger.info("🔄 Initializing output adapters...")
        output_adapter_manager = create_output_adapters(config)
        ServiceRegistry.register("output_adapter_manager", output_adapter_manager)

        if output_adapter_manager.adapters:
            logger.info(
                f"✅ Output adapters registered: {[adapter.__class__.__name__ for adapter in output_adapter_manager.adapters]}"
            )
            # Simple adapter testing
            await test_output_adapters_simple(output_adapter_manager)
        else:
            logger.info("ℹ️ No output adapters configured")

        # 8. Initialize and register LLM
        logger.info("🤖 Setting up LLM...")
        llm = OllamaLLM(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            top_p=config.ollama.top_p,
            top_k=config.ollama.top_k,
            repeat_penalty=config.ollama.repeat_penalty,
        )
        ServiceRegistry.register("llm", llm)
        logger.info(f"✅ LLM registered: {config.ollama.model}")

        # 9. Initialize and register agent
        logger.info("🎭 Creating entity agent...")
        agent = EntityAgent(
            config=config.entity,
            tool_manager=tool_registry,
            chat_storage=storage,
            memory_system=memory_system,
            llm=llm,
            output_adapter_manager=output_adapter_manager,
        )
        await agent.initialize()
        ServiceRegistry.register("agent", agent)
        logger.info("✅ Entity agent registered")

        # 10. Mark registry as fully initialized
        ServiceRegistry.mark_initialized()

        # 11. Setup FastAPI app state (much simpler now)
        app.state.registry = ServiceRegistry
        app.state.agent = agent  # Keep for backward compatibility if needed

        # 12. Attach dynamic router
        router_factory = EntityRouterFactory(
            agent, memory_system, tool_registry, storage
        )
        app.include_router(router_factory.get_router(), prefix="/api/v1")

        # 13. Log success with service summary
        services = ServiceRegistry.list_services()
        logger.info("✅ Entity Agent Service started successfully with ServiceRegistry")
        logger.info(f"🛠️ Registered services: {list(services.keys())}")
        logger.info(f"🔧 Service types: {services}")

        # Test memory system quickly
        try:
            stats = await memory_system.get_memory_stats()
            logger.info(f"🧠 Memory system status: {stats.get('status', 'unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Memory system test failed: {e}")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise
    finally:
        # Cleanup phase - ServiceRegistry handles everything!
        logger.info("👋 Shutting down Entity Agent Service")
        await ServiceRegistry.shutdown()


async def test_output_adapters_simple(output_adapter_manager):
    """Simplified output adapter testing"""
    if not output_adapter_manager or not output_adapter_manager.adapters:
        return

    logger.info("🧪 Testing output adapters...")

    for adapter in output_adapter_manager.adapters:
        if hasattr(adapter, "test_connection"):
            adapter_name = adapter.__class__.__name__
            try:
                if await adapter.test_connection():
                    logger.info(f"✅ {adapter_name} connection test passed")
                else:
                    logger.warning(f"⚠️ {adapter_name} connection test failed")
            except Exception as e:
                logger.error(f"❌ {adapter_name} test failed: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Entity Agent Service",
        version="2.0.0",
        description="Entity Agent with ServiceRegistry Architecture",
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
