# Cognee Memory Integration for Voice Entity Project

This guide shows how to add persistent memory to your voice-enabled AI entity using cognee with local Ollama - no external APIs required.

## What You'll Get

- **Persistent Memory**: Your AI entity remembers all conversations
- **Local Setup**: Everything runs on your local network (Ollama + TTS)
- **Voice Enabled**: Full voice synthesis with memory-enhanced responses
- **Knowledge Graphs**: Cognee builds relationships between conversation concepts
- **Memory Commands**: Interactive memory exploration and search

## Prerequisites

- Existing voice entity project with Ollama and TTS
- Python 3.11+ with Poetry
- Ollama running with at least one chat model
- Network access to your Ollama instance

## Step 1: Install Dependencies

```bash
# Add required packages
poetry add cognee python-dotenv psycopg2-binary pgvector transformers

# Update numpy for cognee compatibility
poetry add "numpy>=1.26.4,<=2.1"
```

## Step 2: Install Embedding Model

Your Ollama instance needs an embedding model for vector operations:

```bash
# SSH to your Ollama machine and run:
ollama pull nomic-embed-text
```

## Step 3: Configure Environment

Create a `.env` file in your project root:

```bash
cat > .env << 'EOF'
LLM_API_KEY=ollama
LLM_PROVIDER=ollama
LLM_MODEL=mistral:7b-instruct
LLM_ENDPOINT=http://YOUR_OLLAMA_IP:11434/v1

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_ENDPOINT=http://YOUR_OLLAMA_IP:11434/api/embeddings
EMBEDDING_API_KEY=ollama
EMBEDDING_DIMENSIONS=768
HUGGINGFACE_TOKENIZER=sentence-transformers/all-MiniLM-L6-v2

COGNEE_DATA_DIR=./cognee_data
EOF
```

Replace `YOUR_OLLAMA_IP` with your Ollama server's IP address.

## Step 4: Enhanced Client Code

Replace your existing `client.py` with this memory-enhanced version:

```python
import os
import requests
import pyaudio
import wave
import io
import numpy as np
import asyncio
import logging
from typing import List, Dict, Any
from rich import print
from scipy.signal import resample_poly
from datetime import datetime

# Load environment variables BEFORE importing cognee
from dotenv import load_dotenv
load_dotenv()

# Now import cognee
import cognee

# Your existing configuration
BASE_TTS_URL = "http://192.168.1.110:8888"
BASE_OLLAMA_URL = "http://192.168.1.110:11434"
VOICE_NAME = "bf_emma"
MODEL = "mistral:7b-instruct"
ENTITY_ID = "jade_demon"

# Your existing system prompt
BASE_SYSTEM_PROMPT = """
You are Jade, a demoness bound to Thomas for 40 years by the Key of Solomon.
[... your existing prompt ...]
"""

class CogneeEntityMemory:
    """Memory-enhanced entity using cognee"""
    
    def __init__(self, entity_id: str = ENTITY_ID):
        self.entity_id = entity_id
        self.conversation_count = 0
        self.memory_initialized = False
    
    async def initialize_memory(self):
        """Initialize cognee memory system"""
        if self.memory_initialized:
            return
        
        try:
            # Add entity profile to memory
            entity_context = f"""
            Entity Profile: {self.entity_id}
            Name: Jade
            Type: Demoness bound by Key of Solomon
            [... your character details ...]
            """
            
            await cognee.add(entity_context)
            await cognee.cognify()
            self.memory_initialized = True
            print("✅ Cognee memory system initialized for Jade")
            
        except Exception as e:
            print(f"❌ Memory initialization failed: {e}")
            raise
    
    async def add_conversation_memory(self, user_input: str, ai_response: str):
        """Store conversation in cognee"""
        self.conversation_count += 1
        
        conversation_memory = f"""
        Conversation #{self.conversation_count}
        Timestamp: {datetime.now().isoformat()}
        Thomas said: "{user_input}"
        Jade responded: "{ai_response}"
        """
        
        await cognee.add(conversation_memory)
        await cognee.cognify()
    
    async def get_memory_context(self, current_input: str) -> str:
        """Get relevant memories for context"""
        search_query = f"Entity {self.entity_id} conversations: {current_input}"
        memories = await cognee.search(search_query)
        
        if memories:
            context = "\n--- Relevant Past Interactions ---\n"
            for i, memory in enumerate(memories[:3], 1):
                truncated = memory[:250] + "..." if len(memory) > 250 else memory
                context += f"{i}. {truncated}\n"
            context += "--- End Past Interactions ---\n"
            return context
        
        return ""
    
    async def search_memories(self, query: str) -> List[str]:
        """Search memories"""
        results = await cognee.search(f"Entity {self.entity_id}: {query}")
        return results[:10]

# Initialize memory system
memory_entity = CogneeEntityMemory()

# Your existing audio functions (unchanged)
def synthesize(text: str, voice_name: str = None) -> bytes:
    # ... your existing TTS code ...

def play_audio(frames, sample_width, channels, rate):
    # ... your existing audio playback code ...

# Enhanced chat function with memory
async def query_ollama_chat_with_memory(history: list, model: str, user_input: str) -> str:
    """Chat with memory context"""
    
    # Get memory context
    memory_context = await memory_entity.get_memory_context(user_input)
    
    # Enhance system prompt
    enhanced_prompt = BASE_SYSTEM_PROMPT
    if memory_context:
        enhanced_prompt += f"\n\n{memory_context}"
    
    # Update system message
    if history and history[0]["role"] == "system":
        history[0]["content"] = enhanced_prompt
    
    # Call Ollama
    payload = {"model": model, "messages": history, "stream": False}
    response = requests.post(f"{BASE_OLLAMA_URL}/api/chat", json=payload)
    response.raise_for_status()
    ai_response = response.json()["message"]["content"].strip()
    
    # Store in memory
    await memory_entity.add_conversation_memory(user_input, ai_response)
    
    return ai_response

def query_ollama_chat(history: list, model: str) -> str:
    """Sync wrapper for memory-enhanced chat"""
    user_input = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(query_ollama_chat_with_memory(history, model, user_input))
    finally:
        loop.close()

def interactive_chat():
    """Main chat loop with memory commands"""
    
    # Initialize memory
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(memory_entity.initialize_memory())
    finally:
        loop.close()
    
    print("🧠 Memory system: ENABLED (Cognee + Local Ollama)")
    print("💡 Special commands:")
    print("   'memory' - Show memory stats")
    print("   'recall <query>' - Search memories")
    
    # Your existing voice setup code...
    
    history = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in {"exit", "quit"}:
            break
        
        # Memory commands
        if user_input.lower() == "memory":
            print(f"🧠 Conversations: {memory_entity.conversation_count}")
            continue
        
        if user_input.lower().startswith("recall "):
            query = user_input[7:].strip()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                memories = loop.run_until_complete(memory_entity.search_memories(query))
                if memories:
                    print(f"🧠 Found {len(memories)} memories:")
                    for i, memory in enumerate(memories[:3], 1):
                        print(f"   {i}. {memory[:200]}...")
                else:
                    print("🧠 No memories found")
            finally:
                loop.close()
            continue
        
        # Regular chat with memory
        history.append({"role": "user", "content": user_input})
        print("🤖 Thinking...")
        reply = query_ollama_chat(history, MODEL)
        print(f"Entity: {reply}")
        
        history.append({"role": "assistant", "content": reply})
        
        # Your existing voice synthesis code...
        # synthesize and play audio...
        
        print(f"✅ Response played. (Conversation #{memory_entity.conversation_count})\n")

if __name__ == "__main__":
    interactive_chat()
```

## Step 5: Test the Integration

Run your enhanced client:

```bash
python client.py
```

You should see:
```
✅ Cognee memory system initialized for Jade
🧠 Memory system: ENABLED (Cognee + Local Ollama)
```

## Step 6: Test Memory Features

Try these interactions:

```
You: Hello Jade, remember this conversation about summoning
Entity: *with disdain* Oh, Thomas graces me with his presence again...

You: memory
🧠 Conversations: 1

You: What did I just say to you?
Entity: *rolls eyes* You just told me to remember our conversation about summoning, as if I could forget your tedious presence.

You: recall summoning
🧠 Found 1 memories:
   1. Conversation #1 - Thomas said: "Hello Jade, remember this conversation about summoning"...
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Client   │    │   Local Ollama   │    │   TTS Server    │
│                 │    │                  │    │                 │
│  • Voice I/O    │◄──►│  • Chat Model    │    │  • Voice Synth  │
│  • Memory Mgmt  │    │  • Embeddings    │    │                 │
│  • Cognee       │    │  • Knowledge     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┼─────────────────────┐
                                 ▼                     ▼
                     ┌──────────────────┐    ┌─────────────────┐
                     │   Cognee Local   │    │   SQLite        │
                     │   Knowledge      │    │   Storage       │
                     │   Graph          │    │                 │
                     └──────────────────┘    └─────────────────┘
```

## Features You Now Have

### Memory Capabilities
- **Persistent Conversations**: All interactions stored and searchable
- **Contextual Responses**: AI references past conversations naturally  
- **Knowledge Graphs**: Relationships between concepts automatically built
- **Semantic Search**: Find relevant memories by meaning, not just keywords

### Interactive Commands
- `memory` - View conversation statistics
- `recall <query>` - Search through conversation history
- `exit`/`quit` - Exit the chat

### Technical Benefits
- **100% Local**: No external API calls (except for initial model downloads)
- **Privacy Preserving**: All conversations stay on your infrastructure
- **Scalable**: Handles hundreds of conversations efficiently
- **Voice Enabled**: Full integration with your existing TTS setup

## Troubleshooting

### Common Issues

**Memory System Disabled**
- Check that all environment variables are set in `.env`
- Verify Ollama is accessible at the specified endpoint
- Ensure embedding model (`nomic-embed-text`) is installed

**Module Not Found Errors**
```bash
poetry add missing-package-name
```

**Ollama Connection Issues**
- Test connection: `curl http://YOUR_OLLAMA_IP:11434/api/tags`
- Verify models are available: `curl http://YOUR_OLLAMA_IP:11434/api/tags | grep -E "(mistral|nomic)"`

**Memory Search Returns No Results**
- Ensure `cognify()` is called after adding memories
- Check that conversations are being stored (use `memory` command)

### Performance Tips

- **Model Selection**: Use instruction-tuned models (mistral:7b-instruct, llama3.1:8b-instruct)
- **Memory Limits**: Adjust context retrieval (currently limited to 3 memories)
- **Storage**: Cognee data stored in `./cognee_data/` directory

## Optional Enhancements

### PostgreSQL Integration
For production use, replace SQLite with PostgreSQL:

```env
VECTOR_DB_PROVIDER=pgvector
VECTOR_DB_URL=postgresql://user:pass@host:5432/db
```

### Additional Models
Experiment with different models for specialized tasks:
- Larger models for better reasoning
- Specialized embedding models for domain-specific content

## Success Metrics

Your integration is successful when you see:
- ✅ Cognee memory system initialized
- ✅ Memory system: ENABLED  
- ✅ Pipeline runs completing successfully
- ✅ Conversations being stored and recalled
- ✅ Voice synthesis working with memory-enhanced responses

You now have a fully functional AI entity with persistent memory, running entirely on your local infrastructure!