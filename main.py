import os
import sys
import asyncio
import threading
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from datetime import datetime
import uvicorn
from rich import print

from src.config import ConfigLoader, EntitySystemConfig
from src.agent import EntityAgent

from src.config import ConfigLoader

config_loader = ConfigLoader()


logging.basicConfig(
    level=getattr(logging, config_loader.load().logging.level.upper()),
    format=config_loader.load().logging.format,
)
logger = logging.getLogger(__name__)

# Global entity agent
entity_agent: Optional[EntityAgent] = None


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    has_memory: bool
    memory_stats: Optional[Dict] = None


class HistoryResponse(BaseModel):
    thread_id: str
    conversations: List[Dict[str, str]]
    has_memory: bool


class ConfigResponse(BaseModel):
    entity: Dict[str, Any]
    database: Dict[str, Any]
    ollama: Dict[str, Any]
    server: Dict[str, Any]
    debug: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the entity agent"""
    global entity_agent
    entity_config = config_loader.load()
    logger.info("🚀 Starting Entity Agentic System...")
    logger.info(
        f"🤖 Entity: {entity_config.entity.name} ({entity_config.entity.entity_id})"
    )
    logger.info(
        f"🔧 Database: {entity_config.database.host}:{entity_config.database.port}"
    )
    logger.info(
        f"🧠 Ollama: {entity_config.ollama.base_url} ({entity_config.ollama.model})"
    )

    # try:
    entity_agent = EntityAgent(config=entity_config)
    await entity_agent.initialize()
    logger.info("✅ Entity agent initialized successfully")
    # except Exception as e:
    #     logger.error(f"❌ Failed to initialize entity agent: {e}")

    yield

    if entity_agent:
        try:
            await entity_agent.close()
            logger.info("✅ Entity agent closed successfully")
        except Exception as e:
            logger.error(f"Error closing entity agent: {e}")


# Create FastAPI app using config and modern lifespan
app = FastAPI(
    title="Entity Agentic System with Vector Memory",
    description=f"Jade the Demoness - An AI entity with {config_loader.load().entity.name}",
    version="2.0.0",
    debug=config_loader.load().debug,
    lifespan=lifespan,
)


@app.post("/reload")
async def reload(
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Reload YAML and INI config files"""
    global entity_agent, config
    config = config_loader.load()
    if entity_agent:
        await entity_agent.close()
    entity_agent = EntityAgent(config=config)
    await entity_agent.initialize()
    return {"message": "Configuration reloaded successfully"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Chat with the entity"""
    try:
        if not entity_agent:
            raise HTTPException(status_code=500, detail="Entity agent not initialized")

        response = await entity_agent.process(request.message, request.thread_id)

        return ChatResponse(
            response=response,
            thread_id=request.thread_id,
            has_memory=entity_agent.has_memory(),
            memory_stats=None,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(
    thread_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Get conversation history for a thread"""
    try:
        if not entity_agent:
            raise HTTPException(status_code=500, detail="Entity agent not initialized")

        conversations = await entity_agent.get_conversation_history(thread_id, limit)

        return HistoryResponse(
            thread_id=thread_id,
            conversations=conversations,
            has_memory=entity_agent.has_memory(),
        )
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{thread_id}")
async def delete_history(
    thread_id: str,
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Delete conversation history for a thread"""
    try:
        if not entity_agent:
            raise HTTPException(status_code=500, detail="Entity agent not initialized")

        success = await entity_agent.delete_conversation(thread_id)

        if success:
            return {"message": f"Conversation history for thread {thread_id} deleted"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to delete conversation history"
            )
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import JSONResponse


@app.get("/config")
async def get_config(
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Get full configuration"""
    return JSONResponse(
        content=current_settings.model_dump(by_alias=True, exclude_none=True)
    )


@app.get("/")
async def root(current_settings: EntitySystemConfig = Depends(config_loader.load)):
    """Root endpoint with system information"""
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {
        "message": "Entity Agentic System v2.0",
        "entity_id": current_settings.entity.entity_id,
        "entity_name": current_settings.entity.name,
        "memory_enabled": memory_status,
        "memory_type": "Vector Memory + PostgreSQL" if memory_status else "None",
        "status": "ready" if entity_agent else "initializing",
        "config": {
            "ollama_model": current_settings.ollama.model,
            "database_host": current_settings.database.host,
            "debug_mode": current_settings.debug,
        },
    }


@app.get("/health")
async def health_check(
    current_settings: EntitySystemConfig = Depends(config_loader.load),
):
    """Health check endpoint"""
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {
        "status": "healthy" if entity_agent else "starting",
        "entity": current_settings.entity.name,
        "entity_id": current_settings.entity.entity_id,
        "memory_enabled": memory_status,
        "timestamp": datetime.now().isoformat(),
        "config_loaded": True,
        "services": {
            "ollama": current_settings.ollama.base_url,
            "database": f"{current_settings.database.host}:{current_settings.database.port}",
        },
    }


# Interactive chat loop for console mode
async def chat_loop():
    """Interactive chat loop with memory support"""
    logger.info("🤖 Entity Agent Chat Loop Started")

    # Wait for agent to initialize
    global entity_agent
    while not entity_agent:
        await asyncio.sleep(0.1)

    memory_status = "with Memory" if entity_agent.has_memory() else "without memory"
    logger.info(f"💾 Running {memory_status}")

    entity_config = config_loader.load()

    print(f"\n🎭 Welcome! You are now talking to {entity_config.entity.name}")
    print(
        f"📊 Personality: Sarcasm {entity_config.entity.sarcasm_level:.1f}, Loyalty {entity_config.entity.loyalty_level:.1f}"
    )
    print("💡 Commands:")
    print("   'exit' or 'quit' - Exit chat")
    if entity_agent.has_memory():
        print("   'history' - Show conversation history")
        print("   'clear' - Clear current conversation")
        print("   'switch <thread_id>' - Switch to different conversation thread")
        print("   'memory' - Show memory statistics")
    print("   'status' - Show agent status")
    print("   'config' - Show current configuration")
    print()

    current_thread = "default"
    if entity_agent.has_memory():
        print(f"📝 Current thread: {current_thread}")

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            if user_input.lower() == "status":
                print(f"🤖 Entity Agent Status:")
                print(
                    f"   Entity: {entity_config.entity.name} ({entity_config.entity.entity_id})"
                )
                print(
                    f"   Ollama: {entity_config.ollama.model} @ {entity_config.ollama.base_url}"
                )
                print(
                    f"   Database: {entity_config.database.host}:{entity_config.database.port}"
                )
                print(
                    f"   Memory: {'Available' if entity_agent.has_memory() else 'None'}"
                )
                print(
                    f"   Thread: {current_thread if entity_agent.has_memory() else 'N/A'}"
                )
                print(f"   Debug: {entity_config.debug}")
                continue

            if user_input.lower() == "config":
                print(f"🔧 Current Configuration:")
                print(f"   Entity ID: {entity_config.entity.entity_id}")
                print(f"   Entity Name: {entity_config.entity.name}")
                print(f"   Sarcasm Level: {entity_config.entity.sarcasm_level}")
                print(f"   Loyalty Level: {entity_config.entity.loyalty_level}")
                print(f"   Anger Level: {entity_config.entity.anger_level}")
                print(f"   Wit Level: {entity_config.entity.wit_level}")
                print(f"   Response Brevity: {entity_config.entity.response_brevity}")
                print(f"   Memory Influence: {entity_config.entity.memory_influence}")
                print(f"   Ollama Model: {entity_config.ollama.model}")
                print(f"   Ollama URL: {entity_config.ollama.base_url}")
                print(
                    f"   Database: {entity_config.database.host}:{entity_config.database.port}/{entity_config.database.name}"
                )
                continue

            if entity_agent.has_memory():
                if user_input.lower() == "memory":
                    try:
                        stats = await entity_agent.get_memory_stats()
                        print(f"🧠 Memory Statistics:")
                        print(f"   Total memories: {stats.get('total_memories', 0)}")
                        print(
                            f"   Total conversations: {stats.get('total_conversations', 0)}"
                        )
                        print(f"   Memory types: {stats.get('memory_types', {})}")
                        print(f"   Emotions: {stats.get('emotions', {})}")
                        print(
                            f"   Top topics: {dict(list(stats.get('top_topics', {}).items())[:5])}"
                        )
                        print(f"   Backend: {stats.get('backend', 'unknown')}")
                    except Exception as e:
                        print(f"❌ Error getting memory stats: {e}")
                    continue

                if user_input.lower() == "history":
                    conversations = await entity_agent.get_conversation_history(
                        current_thread, limit=10
                    )
                    if conversations:
                        print(f"📚 History for thread '{current_thread}':")
                        for line in conversations[-10:]:
                            content = line[:80] + "..." if len(line) > 80 else line
                            print(f"   💬 {content}")
                    else:
                        print("📚 No conversation history found")
                    continue

                if user_input.lower() == "clear":
                    success = await entity_agent.delete_conversation(current_thread)
                    if success:
                        print(
                            f"🧹 Conversation history cleared for thread '{current_thread}'"
                        )
                    else:
                        print("❌ Failed to clear conversation history")
                    continue

                if user_input.lower().startswith("switch "):
                    new_thread = user_input[7:].strip()
                    if new_thread:
                        current_thread = new_thread
                        print(f"📝 Switched to thread: {current_thread}")
                    else:
                        print("❌ Please specify a thread ID")
                    continue

            if not user_input:
                continue

            print("🤖 Thinking...")

            # Process message
            response = await entity_agent.process(user_input, current_thread)
            print(f"{entity_config.entity.name}: {response}")
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Chat loop error: {e}")
            print(f"❌ Error: {e}")


def run_chat_loop():
    """Run the chat loop in a separate thread"""
    asyncio.run(chat_loop())


def start_chat_thread():
    """Start chat loop in background thread"""
    chat_thread = threading.Thread(target=run_chat_loop, daemon=True)
    chat_thread.start()
    return chat_thread


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # Load configuration
    entity_config = config_loader.load()

    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "server"

    if mode == "chat":
        # Run only the chat loop
        logger.info("🚀 Starting chat-only mode...")
        entity_agent = EntityAgent(config=entity_config)
        asyncio.run(chat_loop())

    elif mode == "both":
        # Run both FastAPI server and chat loop
        logger.info("🚀 Starting both FastAPI server and chat loop...")

        # Start chat loop in background
        start_chat_thread()

        # Start FastAPI server using config
        uvicorn.run(
            app,
            host=entity_config.server.host,
            port=entity_config.server.port,
            reload=entity_config.server.reload,
            log_level=entity_config.server.log_level,
        )

    elif mode == "simple":
        # Simple test mode
        logger.info("🧪 Simple test mode...")
        print("Testing basic imports...")
        try:
            from src.agent import EntityAgent

            print("✅ EntityAgent import successful")

            agent = EntityAgent(config=entity_config)
            print("✅ EntityAgent creation successful")
            print(f"   Entity: {entity_config.entity.name}")
            print(f"   Model: {entity_config.ollama.model}")
            print(f"   Debug: {entity_config.debug}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

    elif mode == "config":
        # Show configuration
        logger.info("🔧 Configuration Details:")
        print("\n" + "=" * 50)
        print("ENTITY CONFIGURATION")
        print("=" * 50)
        print(f"Entity ID: {entity_config.entity.entity_id}")
        print(f"Entity Name: {entity_config.entity.name}")
        print(f"Sarcasm Level: {entity_config.entity.sarcasm_level}")
        print(f"Loyalty Level: {entity_config.entity.loyalty_level}")
        print(f"Anger Level: {entity_config.entity.anger_level}")
        print(f"Wit Level: {entity_config.entity.wit_level}")
        print(f"Response Brevity: {entity_config.entity.response_brevity}")
        print(f"Memory Influence: {entity_config.entity.memory_influence}")

        print("\n" + "=" * 50)
        print("OLLAMA CONFIGURATION")
        print("=" * 50)
        print(f"Base URL: {entity_config.ollama.base_url}")
        print(f"Model: {entity_config.ollama.model}")
        print(f"Temperature: {entity_config.ollama.temperature}")
        print(f"Top P: {entity_config.ollama.top_p}")
        print(f"Top K: {entity_config.ollama.top_k}")
        print(f"Repeat Penalty: {entity_config.ollama.repeat_penalty}")

        print("\n" + "=" * 50)
        print("DATABASE CONFIGURATION")
        print("=" * 50)
        print(f"Host: {entity_config.database.host}")
        print(f"Port: {entity_config.database.port}")
        print(f"Database: {entity_config.database.name}")
        print(f"Username: {entity_config.database.username}")
        print(
            f"Connection String: {entity_config.database.connection_string.replace(entity_config.database.password, '***')}"
        )

        print("\n" + "=" * 50)
        print("SERVER CONFIGURATION")
        print("=" * 50)
        print(f"Host: {entity_config.server.host}")
        print(f"Port: {entity_config.server.port}")
        print(f"Reload: {entity_config.server.reload}")
        print(f"Log Level: {entity_config.server.log_level}")

        print("\n" + "=" * 50)
        print(f"Debug Mode: {entity_config.debug}")

    else:
        # Default: run only FastAPI server
        logger.info("🚀 Starting FastAPI server...")
        logger.info("💡 Available modes:")
        logger.info("   python main.py chat    - Chat-only mode")
        logger.info("   python main.py both    - Server + chat")
        logger.info("   python main.py simple  - Simple test mode")
        logger.info("   python main.py config  - Show configuration")
        logger.info("   python main.py server  - Server only (default)")

        uvicorn.run(
            app,
            host=entity_config.server.host,
            port=entity_config.server.port,
            reload=entity_config.server.reload,
            log_level=entity_config.server.log_level,
        )
