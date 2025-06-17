from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from entity.agent import EntityAgent
from typing import Optional, List, Dict
import os
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Entity Agentic System with PostgreSQL Memory")

# Initialize entity agent
entity_agent = None


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    has_memory: bool


class HistoryResponse(BaseModel):
    thread_id: str
    conversations: List[Dict[str, str]]
    has_memory: bool


@app.on_event("startup")
async def startup_event():
    global entity_agent
    entity_agent = EntityAgent()
    await entity_agent.initialize()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not entity_agent:
            raise HTTPException(status_code=500, detail="Entity agent not initialized")

        response = await entity_agent.process(request.message, request.thread_id)

        return ChatResponse(
            response=response,
            thread_id=request.thread_id,
            has_memory=entity_agent.has_memory(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{thread_id}", response_model=HistoryResponse)
async def get_history(thread_id: str, limit: int = Query(default=10, ge=1, le=100)):
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
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{thread_id}")
async def delete_history(thread_id: str):
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {
        "message": "Entity Agentic System",
        "entity_id": "jade",
        "memory_enabled": memory_status,
        "memory_type": "PostgreSQL" if memory_status else "None",
    }


@app.get("/health")
async def health_check():
    memory_status = entity_agent.has_memory() if entity_agent else False
    return {"status": "healthy", "entity": "jade", "memory_enabled": memory_status}


async def chat_loop():
    """Interactive chat loop with memory support"""
    print("🤖 Entity Agent Chat Loop Started")

    # Wait for agent to initialize
    global entity_agent
    while not entity_agent:
        await asyncio.sleep(0.1)

    memory_status = (
        "with PostgreSQL memory" if entity_agent.has_memory() else "without memory"
    )
    print(f"💾 Running {memory_status}")

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
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        if user_input.lower() == "status":
            print(f"🤖 Entity Agent Status:")
            print(f"   Model: {entity_agent.model}")
            print(f"   Memory: {'PostgreSQL' if entity_agent.has_memory() else 'None'}")
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
                        print(f"   {role_icon} {conv['content'][:80]}...")
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

        # Process message with or without memory
        if entity_agent.has_memory():
            response = await entity_agent.process(user_input, current_thread)
        else:
            response = await entity_agent.process(user_input)

        print(f"Jade: {response}")
        print()


def run_chat_loop():
    """Run the chat loop in a separate thread"""
    asyncio.run(chat_loop())


def start_chat_thread():
    """Start chat loop in background thread"""
    chat_thread = threading.Thread(target=run_chat_loop, daemon=True)
    chat_thread.start()
    return chat_thread


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Run only the chat loop
        print("🚀 Starting chat-only mode...")
        entity_agent = EntityAgent()
        asyncio.run(chat_loop())

    elif len(sys.argv) > 1 and sys.argv[1] == "both":
        # Run both FastAPI server and chat loop
        print("🚀 Starting both FastAPI server and chat loop...")

        # Start chat loop in background
        start_chat_thread()

        # Start FastAPI server
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)

    else:
        # Default: run only FastAPI server
        print("🚀 Starting FastAPI server...")
        print("💡 Use 'python main.py chat' for chat-only mode")
        print("💡 Use 'python main.py both' for server + chat")
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
