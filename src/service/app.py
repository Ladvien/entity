# src/service/app.py - ENHANCED WITH OUTPUT ADAPTERS

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
from src.adapters import create_output_adapters  # NEW IMPORT

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


def inject_memory_into_tools_comprehensive(
    tool_manager: ToolManager, memory_system: VectorMemorySystem
):
    """Comprehensive memory injection with multiple strategies"""
    try:
        injection_count = 0

        # Strategy 1: Store globally in tools module for easy access
        import src.tools.tools as tools_module

        tools_module._global_memory_system = memory_system
        logger.info("✅ Memory system stored globally in tools module")

        # Strategy 2: Direct injection into tool instances
        all_tools = tool_manager.get_all_tools()
        logger.info(f"🔧 Injecting memory system into {len(all_tools)} tools...")

        for tool in all_tools:
            tool_name = getattr(tool, "name", "unknown")

            # Check if this is a memory-related tool
            if any(
                keyword in tool_name.lower()
                for keyword in ["memory", "search", "store"]
            ):
                try:
                    # Multiple injection strategies for maximum compatibility

                    # Method 1: Direct attribute setting
                    setattr(tool, "_memory_system", memory_system)

                    # Method 2: Try to set on the underlying function if it exists
                    if hasattr(tool, "func"):
                        setattr(tool.func, "_memory_system", memory_system)

                    # Method 3: Try to set on args if they exist
                    if hasattr(tool, "args_schema"):
                        setattr(tool.args_schema, "_memory_system", memory_system)

                    # Method 4: If this is a StructuredTool, try to reach the original instance
                    if hasattr(tool, "_run") and hasattr(tool._run, "__self__"):
                        setattr(tool._run.__self__, "_memory_system", memory_system)

                    injection_count += 1
                    logger.info(f"✅ Memory system injected into {tool_name} tool")

                except Exception as e:
                    logger.warning(f"⚠️ Could not inject memory into {tool_name}: {e}")

        # Strategy 3: Store in tool manager itself
        setattr(tool_manager, "_memory_system", memory_system)

        # Strategy 4: Create a registry of memory tools for easier access
        memory_tools = {}
        for tool in all_tools:
            tool_name = getattr(tool, "name", "unknown")
            if any(
                keyword in tool_name.lower()
                for keyword in ["memory", "search", "store"]
            ):
                memory_tools[tool_name] = tool

        tools_module._memory_tools_registry = memory_tools

        logger.info(
            f"✅ Memory injection completed successfully - {injection_count} tools enhanced"
        )
        logger.info(f"🧠 Memory-related tools: {list(memory_tools.keys())}")

        # Verify injection worked
        verify_memory_injection(tool_manager, memory_system)

    except Exception as e:
        logger.error(f"❌ Memory injection failed: {e}", exc_info=True)


def verify_memory_injection(
    tool_manager: ToolManager, memory_system: VectorMemorySystem
):
    """Verify that memory injection worked properly"""
    try:
        # Check global storage
        import src.tools.tools as tools_module

        if hasattr(tools_module, "_global_memory_system"):
            logger.info("✅ Global memory system verification: SUCCESS")
        else:
            logger.warning("⚠️ Global memory system verification: FAILED")

        # Check tool-specific injection
        memory_tools_found = 0
        all_tools = tool_manager.get_all_tools()

        for tool in all_tools:
            tool_name = getattr(tool, "name", "unknown")
            if any(
                keyword in tool_name.lower()
                for keyword in ["memory", "search", "store"]
            ):
                if hasattr(tool, "_memory_system"):
                    memory_tools_found += 1
                    logger.debug(f"✅ {tool_name} has direct memory system access")
                else:
                    logger.warning(f"⚠️ {tool_name} missing direct memory system access")

        logger.info(
            f"✅ Memory injection verification: {memory_tools_found} tools have memory access"
        )

    except Exception as e:
        logger.error(f"❌ Memory injection verification failed: {e}")


async def test_output_adapters(output_adapter_manager, config):
    """Test output adapters during startup"""
    if not output_adapter_manager or not output_adapter_manager.adapters:
        logger.info("🔄 No output adapters to test")
        return

    logger.info("🧪 Testing output adapters...")

    try:
        # Test TTS adapter if present
        for adapter in output_adapter_manager.adapters:
            if hasattr(adapter, "test_connection"):
                adapter_name = adapter.__class__.__name__
                logger.info(f"🔍 Testing {adapter_name}...")

                if await adapter.test_connection():
                    logger.info(f"✅ {adapter_name} connection test passed")

                    # Test voice listing for TTS
                    if hasattr(adapter, "list_available_voices"):
                        voices = await adapter.list_available_voices()
                        logger.info(f"🎙️ Available voices: {len(voices)}")
                else:
                    logger.warning(f"⚠️ {adapter_name} connection test failed")

    except Exception as e:
        logger.error(f"❌ Output adapter testing failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with enhanced memory injection and output adapters"""
    logger.info("🚀 Starting Entity Agent Service with Enhanced Features")

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

    # Setup tool registry
    logger.info(f"🔧 Loading tools from: {config.tools.plugin_path}")
    tool_registry = ToolManager.setup(
        plugin_directory=config.tools.plugin_path,
        enabled_tools=getattr(config.tools, "enabled", None),
    )
    logger.info(
        f"✅ Tool registry initialized with {len(tool_registry.list_tool_names())} tools: {tool_registry.list_tool_names()}"
    )

    # Enhanced memory injection
    logger.info("🧠 Starting comprehensive memory injection...")
    inject_memory_into_tools_comprehensive(tool_registry, memory_system)

    # NEW: Initialize output adapters
    logger.info("🔄 Initializing output adapters...")
    output_adapter_manager = create_output_adapters(config)

    if output_adapter_manager.adapters:
        logger.info(
            f"✅ Output adapters initialized: {[adapter.__class__.__name__ for adapter in output_adapter_manager.adapters]}"
        )
        await test_output_adapters(output_adapter_manager, config)
    else:
        logger.info("ℹ️ No output adapters configured")

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

    # Initialize agent with output adapters
    agent = EntityAgent(
        config=config.entity,
        tool_manager=tool_registry,
        chat_storage=storage,
        memory_system=memory_system,
        llm=llm,
        output_adapter_manager=output_adapter_manager,  # NEW PARAMETER
    )
    await agent.initialize()
    logger.info("✅ Entity agent initialized with output adapters")

    # Attach everything to app.state
    app.state.config = config
    app.state.agent = agent
    app.state.storage = storage
    app.state.memory_system = memory_system
    app.state.tool_registry = tool_registry
    app.state.db_connection = db_connection
    app.state.output_adapter_manager = output_adapter_manager  # NEW STATE

    # Attach dynamic router
    router_factory = EntityRouterFactory(agent, memory_system, tool_registry, storage)
    app.include_router(router_factory.get_router(), prefix="/api/v1")

    logger.info("✅ Entity Agent Service started successfully")
    logger.info(f"🛠️ Available tools: {tool_registry.list_tool_names()}")

    # Enhanced output adapter info
    if output_adapter_manager.adapters:
        adapter_names = [
            adapter.__class__.__name__ for adapter in output_adapter_manager.adapters
        ]
        logger.info(f"🔄 Active output adapters: {adapter_names}")

    # Test memory system quickly
    try:
        stats = await memory_system.get_memory_stats()
        logger.info(f"🧠 Memory system status: {stats.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"⚠️ Memory system test failed: {e}")

    yield

    # Cleanup phase
    logger.info("👋 Shutting down Entity Agent Service")

    try:
        await agent.cleanup()  # This will also close output adapters
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
        description="Entity Agent with PostgreSQL Vector Memory and Output Adapters",
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
