import os
import sys
import asyncio
import threading
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uvicorn

# Import our configuration system - using your current structure
try:
    from entity.config import Settings, load_settings, get_settings_dependency
except ImportError:
    # Fallback to simple configuration if config module doesn't exist
    print("⚠️  Configuration module not found. Creating minimal setup...")

    # Create a minimal configuration class
    class Settings:
        def __init__(self):
            self.entity = type(
                "Entity",
                (),
                {
                    "entity_id": "jade_demon",
                    "name": "Jade",
                    "sarcasm_level": 0.8,
                    "loyalty_level": 0.6,
                    "anger_level": 0.7,
                    "wit_level": 0.9,
                },
            )()
            self.database = type(
                "Database",
                (),
                {
                    "host": "192.168.1.104",
                    "port": 5432,
                    "name": "entity_memory",
                    "username": "entity_user",
                    "password": "your_secure_password",
                },
            )()
            self.server = type(
                "Server",
                (),
                {"host": "0.0.0.0", "port": 8000, "reload": False, "log_level": "info"},
            )()
            self.debug = False

    def load_settings(config_path="config.yaml"):
        return Settings()

    def get_settings_dependency():
        return Settings()


from entity.agent import EntityAgent

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = load_settings()

# Create FastAPI app
app = FastAPI(
    title="Entity Agentic System with Vector Memory",
    description="Jade the Demoness - An AI entity with PostgreSQL + pgvector memory",
    version="2.0.0",
    debug=settings.debug,
)

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


@app.on_event("startup")
async def startup_event():
    """Initialize the entity agent on startup"""
    global entity_agent

    logger.info("🚀 Starting Entity Agentic System...")
    logger.info(f"🤖 Entity: {settings.entity.name} ({settings.entity.entity_id})")

    try:
        entity_agent = EntityAgent()  # Use original agent for now
        # If your agent supports settings, use: EntityAgent(settings=settings)
        await entity_agent.initialize()
        logger.info("✅ Entity agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize entity agent: {e}")
        # Don't raise - allow server to start without agent for debugging


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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
async def get_history(thread_id: str, limit: int = Query(default=10, ge=1, le=100)):
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
async def delete_history(thread_id: str):
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


@app.get("/")
async def root():
    """Root endpoint with system information"""
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {
        "message": "Entity Agentic System v2.0",
        "entity_id": settings.entity.entity_id,
        "entity_name": settings.entity.name,
        "memory_enabled": memory_status,
        "memory_type": "PostgreSQL + pgvector" if memory_status else "None",
        "status": "ready" if entity_agent else "initializing",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {
        "status": "healthy" if entity_agent else "starting",
        "entity": settings.entity.name,
        "entity_id": settings.entity.entity_id,
        "memory_enabled": memory_status,
        "timestamp": datetime.now().isoformat(),
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

    print(f"\n🎭 Welcome! You are now talking to {settings.entity.name}")
    print("💡 Commands:")
    print("   'exit' or 'quit' - Exit chat")
    if entity_agent.has_memory():
        print("   'history' - Show conversation history")
        print("   'clear' - Clear current conversation")
        print("   'switch <thread_id>' - Switch to different conversation thread")
    print("   'status' - Show agent status")
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
                print(f"   Entity: {settings.entity.name}")
                print(
                    f"   Memory: {'Available' if entity_agent.has_memory() else 'None'}"
                )
                print(
                    f"   Thread: {current_thread if entity_agent.has_memory() else 'N/A'}"
                )
                continue

            if entity_agent.has_memory():
                if user_input.lower() == "history":
                    conversations = await entity_agent.get_conversation_history(
                        current_thread, limit=10
                    )
                    if conversations:
                        print(f"📚 History for thread '{current_thread}':")
                        for conv in conversations[-10:]:  # Show last 10
                            role_icon = "🧑" if conv["role"] == "user" else "😈"
                            content = (
                                conv["content"][:80] + "..."
                                if len(conv["content"]) > 80
                                else conv["content"]
                            )
                            print(f"   {role_icon} {content}")
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
            print(f"{settings.entity.name}: {response}")
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

    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "server"

    if mode == "chat":
        # Run only the chat loop
        logger.info("🚀 Starting chat-only mode...")
        entity_agent = EntityAgent()
        asyncio.run(chat_loop())

    elif mode == "both":
        # Run both FastAPI server and chat loop
        logger.info("🚀 Starting both FastAPI server and chat loop...")

        # Start chat loop in background
        start_chat_thread()

        # Start FastAPI server
        uvicorn.run(
            app,
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload,
            log_level=settings.server.log_level,
        )

    elif mode == "simple":
        # Simple test mode
        logger.info("🧪 Simple test mode...")
        print("Testing basic imports...")
        try:
            from entity.agent import EntityAgent

            print("✅ EntityAgent import successful")

            agent = EntityAgent()
            print("✅ EntityAgent creation successful")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

    else:
        # Default: run only FastAPI server
        logger.info("🚀 Starting FastAPI server...")
        logger.info("💡 Available modes:")
        logger.info("   python main.py chat    - Chat-only mode")
        logger.info("   python main.py both    - Server + chat")
        logger.info("   python main.py simple  - Simple test mode")
        logger.info("   python main.py server  - Server only (default)")

        uvicorn.run(
            app,
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload,
            log_level=settings.server.log_level,
        )
