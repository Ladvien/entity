from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from entity.entity_agenty import EntityAgent
import os
import asyncio
import threading
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Entity Agentic System")
entity_agent = EntityAgent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await entity_agent.process(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Entity Agentic System"}


async def chat_loop():
    """Interactive chat loop for direct terminal interaction"""
    print("🤖 Entity Agent Chat Loop Started")
    print("💡 Commands:")
    print("   'exit' or 'quit' - Exit chat")
    print("   'clear' - Clear conversation history")
    print("   'status' - Show agent status")
    print()

    conversation_history = []

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            if user_input.lower() == "clear":
                conversation_history.clear()
                print("🧹 Conversation history cleared")
                continue

            if user_input.lower() == "status":
                print(f"🤖 Entity Agent Status:")
                print(f"   Model: {getattr(entity_agent, 'model', 'Unknown')}")
                print(f"   Conversations: {len(conversation_history)}")
                continue

            if not user_input:
                continue

            print("🤖 Thinking...")

            # Process message with entity agent
            response = await entity_agent.process(user_input)

            # Store conversation
            conversation_history.append(
                {
                    "user": user_input,
                    "assistant": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            print(f"Jade: {response}")
            print()

        except KeyboardInterrupt:
            print("\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.")


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
    from datetime import datetime

    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Run only the chat loop
        print("🚀 Starting chat-only mode...")
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
        print("🚀 Starting FastAPI server only...")
        print("💡 Use 'python main.py chat' for chat-only mode")
        print("💡 Use 'python main.py both' for server + chat")
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
