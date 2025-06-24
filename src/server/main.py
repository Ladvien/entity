# src/server/main.py

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from langchain_ollama import OllamaLLM
from rich import print

from src.plugins.registry import ToolManager
from src.server.agent import EntityAgent
from src.core.config import EntityServerConfig
from src.db.connection import (
    close_global_db_connection,
    initialize_global_db_connection,
)
from src.memory.memory_system import MemorySystem
from src.adapters import create_adapters
from src.core.registry import ServiceRegistry
from src.server.routes import EntityRouterFactory

# NEW: Import prompt plugin system
from src.plugins.prompts.manager import PromptPluginManager
from src.plugins.prompts.context import PromptContext

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
    config = EntityServerConfig.config_from_file()

    print(config)

    setup_logging(config)
    ServiceRegistry.register("config", config)

    # NEW: Initialize Prompt Plugin Manager
    logger.info("🧩 Initializing prompt plugin system...")
    prompt_manager = PromptPluginManager()

    # Auto-discover plugins from the plugins directory
    prompt_manager.auto_discover_plugins("src/plugins/prompts/strategies")

    # Load the configured prompt plugin
    prompt_plugin_name = getattr(config.entity.prompt, "plugin", "react")
    try:
        prompt_plugin = prompt_manager.get_plugin(prompt_plugin_name)
        logger.info(f"✅ Loaded prompt plugin: {prompt_plugin_name}")
    except Exception as e:
        logger.error(f"❌ Failed to load prompt plugin '{prompt_plugin_name}': {e}")

    ServiceRegistry.register("prompt_manager", prompt_manager)
    ServiceRegistry.register("prompt_plugin", prompt_plugin)

    # NEW: Validate prompt using plugin's validator
    logger.info("🔍 Validating prompt configuration...")
    validation_result = prompt_plugin.validate_prompt()

    if not validation_result.is_valid:
        logger.error("❌ Prompt validation failed! Issues found:")
        for issue in validation_result.issues:
            logger.error(f"  - {issue.category}: {issue.message}")
        logger.error("💡 Server will continue but may experience parsing errors.")
    else:
        logger.info("✅ Prompt validation passed!")

    # Initialize database (FIXED: use 'data' instead of 'database_config')
    logger.info("🔗 Initializing global database connection...")
    logger.debug(f"Database config: {config.data}")
    db = await initialize_global_db_connection(config.data)
    ServiceRegistry.register("db", db)

    # Initialize memory system (FIXED: use 'data' instead of 'database_config')
    memory_system = MemorySystem(
        memory_config=config.memory,
        database_config=config.data,
    )
    await memory_system.initialize()
    ServiceRegistry.register("memory", memory_system)

    # Initialize tool manager
    tool_manager = ToolManager(config.tools)
    tool_manager.load_plugins_from_config(config.tools.plugin_path)

    for tool in tool_manager.get_all_tools():
        logger.info(f"✅ Registered tool: {tool.name}")

    ServiceRegistry.register("tools", tool_manager)

    # NEW: Generate dynamic prompt using the plugin
    logger.info("🎭 Generating dynamic prompt...")
    prompt_context = PromptContext(
        personality=config.entity,
        tools=tool_manager.get_all_tools(),
        memory_config=config.memory,
        custom_variables={},
    )

    try:
        generated_prompt = prompt_plugin.generate_prompt(prompt_context)
        logger.info("✅ Prompt generated successfully")
        logger.debug(f"Generated prompt preview: {generated_prompt[:200]}...")
    except Exception as e:
        logger.error(f"❌ Prompt generation failed: {e}")

    # Initialize LLM with generated prompt
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
        base_template=generated_prompt.strip(),
    )
    ServiceRegistry.register("llm", llm)

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

    # Initialize agent with adapters and prompt plugin
    agent = EntityAgent(
        config=config.entity,
        tool_manager=tool_manager,
        llm=llm,
        memory_system=memory_system,
        output_adapter_manager=output_adapter_manager,
        prompt_plugin=prompt_plugin,  # NEW: Pass prompt plugin to agent
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
