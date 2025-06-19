import sys
import asyncio
import logging
from fastapi import FastAPI
import uvicorn

from langchain_ollama import OllamaLLM

from src.service.agent import EntityAgent
from src.service.config import load_config
from src.service.routes import EntityRouterFactory
from src.storage import create_storage
from src.tools.memory import VectorMemorySystem
from src.tools.tools import setup_tools

from src.cli.client import EntityAPIClient
from src.cli.chat_interface import ChatInterface


def setup_logging():
    """Setup logging configuration."""
    try:
        config = load_config("config.yaml")
        logging.basicConfig(
            level=getattr(logging, config.logging.level.upper()),
            format=config.logging.format,
        )
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to load logging config: {e}")


async def create_app_service():
    """Builds the app service components: agent, memory, tools, etc."""
    config = load_config("config.yaml")

    # Initialize memory system
    memory = VectorMemorySystem(
        memory_config=config.memory, database_config=config.database
    )
    await memory.initialize()

    # Initialize chat history storage
    storage = await create_storage(config.storage, config.database)

    # Register tools
    tools = await setup_tools(config.tools, memory)

    # Inject LLM
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
    )

    # Build agent with injected LLM
    agent = EntityAgent(
        config=config.entity,
        tool_registry=tools,
        storage=storage,
        memory_system=memory,
        llm=llm,
    )
    await agent.initialize()

    return config, agent, memory, tools, storage


def run_server_mode():
    """Run FastAPI app using Uvicorn."""

    async def lifespan(app: FastAPI):
        unified_config, agent, memory, tools, storage = await create_app_service()

        router_factory = EntityRouterFactory(agent, memory, tools, storage)
        app.include_router(router_factory.get_router(), prefix="/api/v1")
        app.state.agent = agent
        app.state.memory_system = memory
        app.state.tool_registry = tools
        app.state.storage = storage
        app.state.config = unified_config

        yield
        await agent.cleanup()
        await memory.close()

    # 👇 Temporarily load config just to get `debug`, `host`, etc.
    initial_config = load_config("config.yaml")

    app = FastAPI(
        title="Entity Agentic System",
        version="2.0.0",
        description="Jade the Demoness - Vector Memory AI Agent",
        debug=initial_config.debug,
        lifespan=lifespan,
    )

    uvicorn.run(
        app,
        host=initial_config.server.host,
        port=initial_config.server.port,
        reload=initial_config.server.reload,
        log_level=initial_config.server.log_level,
    )


async def run_chat_mode():
    config = load_config("config.yaml")
    client = EntityAPIClient(
        base_url=f"http://{config.server.host}:{config.server.port}"
    )
    interface = ChatInterface(client, config={"save_locally": True})
    await interface.run()


def run_simple_test():
    config = load_config("config.yaml")
    print("✅ Configuration loaded")
    print(f"Entity Name: {config.entity.name}")
    print(f"Model: {config.ollama.model}")
    print(f"Database: {config.database.name}@{config.database.host}")


async def run_both_mode():
    """Run both the FastAPI server and the chat CLI"""
    import threading

    def start_uvicorn():
        run_server_mode()

    # Start server in a background thread
    server_thread = threading.Thread(target=start_uvicorn, daemon=True)
    server_thread.start()

    # Wait a moment for the server to start
    await asyncio.sleep(3)

    # Start the chat CLI
    await run_chat_mode()


def show_config():
    config = load_config("config.yaml")
    print("=== CONFIG ===")
    print(config.model_dump_json(indent=2))


def main():
    setup_logging()
    mode = sys.argv[1] if len(sys.argv) > 1 else "server"
    try:
        if mode == "chat":
            asyncio.run(run_chat_mode())
        elif mode == "server":
            run_server_mode()
        elif mode == "both":
            asyncio.run(run_both_mode())
        elif mode == "simple":
            run_simple_test()
        elif mode == "config":
            show_config()
        else:
            print("Unknown mode:", mode)
    except Exception as e:
        logging.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
