# 01 - Hello Agent 👋

**Your First Entity Agent in Under 60 Seconds**

This is the simplest possible Entity agent - perfect for understanding the basics.

## What This Example Teaches

- 🚀 **Zero-config agent creation** using Entity defaults
- 🧠 **Automatic LLM setup** (Ollama or cloud APIs)
- 💾 **Built-in memory** that persists between conversations
- 📝 **Interactive chat** interface

## The Complete Code

```python
#!/usr/bin/env python3
"""
The simplest possible Entity agent.
Demonstrates zero-configuration setup with automatic resource management.
"""

import asyncio
from entity import Agent
from entity.defaults import load_defaults

async def main():
    """Create and run your first Entity agent."""

    print("🤖 Creating your first Entity agent...")

    # Load default resources (LLM, Memory, Logging, Storage)
    # This automatically sets up everything you need
    resources = load_defaults()

    # Create an agent with these resources
    agent = Agent(resources=resources)

    print("✅ Agent created successfully!")
    print("💬 Starting interactive chat (type 'quit' to exit)...")
    print("-" * 50)

    # Start interactive chat session
    # Empty string triggers Entity's built-in interactive mode
    await agent.chat("")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Your agent session has ended.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Ollama is running or your API keys are set!")
```

## What Happens When You Run This

1. **Resource Setup**: Entity automatically configures:
   - 🧠 **LLM** (Ollama locally or cloud API)
   - 💾 **Memory** (DuckDB database for persistence)
   - 📊 **Logging** (Structured logging to console/file)
   - 📁 **Storage** (File system for agent data)

2. **Interactive Session**: Your agent can:
   - Answer questions intelligently
   - Remember conversation history
   - Handle complex multi-turn dialogues
   - Maintain context across sessions

3. **Zero Configuration**: No YAML, no setup files, just works!

## Try These Conversations

```
👤 You: Hello! What can you do?
🤖 Agent: Hi! I'm an AI assistant powered by Entity Framework. I can help with...

👤 You: Remember that my name is Alice
🤖 Agent: Got it! I'll remember that your name is Alice.

👤 You: What's my name?
🤖 Agent: Your name is Alice, as you told me earlier.

👤 You: Tell me a joke about programming
🤖 Agent: Why do programmers prefer dark mode? Because light attracts bugs! 🐛
```

## Running the Example

```bash
# Navigate to the example directory
cd examples/01_hello_agent

# Install Entity if you haven't already
pip install entity-core

# Run the example
python hello_agent.py
```

## Troubleshooting

### "No LLM available" Error
```bash
# Option 1: Install Ollama (recommended)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama serve

# Option 2: Use cloud API
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
```

### "Permission denied" or "Port in use"
```bash
# Check if another process is using the default ports
lsof -i :11434  # Ollama default port

# Kill existing Ollama processes if needed
pkill ollama
ollama serve
```

## What Makes This Special?

Unlike other AI frameworks that require extensive setup:

### Traditional Approach
```python
# 50+ lines of setup code required:
# - Manual LLM client configuration
# - Database connection setup
# - Memory management
# - Error handling
# - Logging configuration
# - Session management
# - Input/output handling
```

### Entity Approach
```python
# Just 3 essential lines:
resources = load_defaults()
agent = Agent(resources=resources)
await agent.chat("")
```

Entity handles all the complexity automatically while remaining fully customizable when you need it.

## Next Steps

1. **Try the agent**: Run it and have a conversation
2. **Experiment**: Ask different types of questions
3. **Test persistence**: Exit and restart - your agent remembers!
4. **Ready for more?**: Check out [02_agent_personality](../02_agent_personality/) to customize your agent

## Key Concepts Learned

✅ **Entity Agents** are created with `Agent(resources=resources)`
✅ **Default Resources** provide everything needed with zero config
✅ **Interactive Chat** is triggered with `await agent.chat("")`
✅ **Memory Persistence** happens automatically
✅ **Error Handling** is built-in and graceful

---

**🎉 Congratulations!** You've just created your first Entity agent. This same pattern scales from simple chatbots to complex multi-agent systems.

*Next: [Agent with Personality](../02_agent_personality/) →*
