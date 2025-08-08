# 5-Minute Quick Start Guide 🚀

**From Zero to AI Agent in Under 5 Minutes**

Welcome to Entity Framework! This guide will get you from installation to a working AI agent in just 5 minutes. No configuration required, no complex setup - just pure AI power.

## ⏱️ **Timeline: 5 Minutes Total**

- **Minute 1**: Installation and setup
- **Minute 2**: Your first agent
- **Minute 3**: Adding personality
- **Minute 4**: Giving it superpowers with tools
- **Minute 5**: Exploring what you've built

Let's go! ⚡

---

## 🚀 **Minute 1: Installation & Setup**

### Install Entity Framework
```bash
# Quick install (30 seconds)
pip install entity-core

# Or use uv for speed
uv add entity-core
```

### Set Up Your LLM (Optional)
Entity works with local or cloud LLMs:

```bash
# Option A: Local LLM (Recommended)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama serve

# Option B: Cloud API (Set environment variable)
export OPENAI_API_KEY="your-key-here"
```

**⏰ Time check: 1 minute** ✅

---

## 🤖 **Minute 2: Your First Agent**

Create your first intelligent agent with just 3 lines of code:

### `hello_agent.py`
```python
import asyncio
from entity import Agent
from entity.defaults import load_defaults

async def main():
    # This single line sets up everything: LLM, memory, logging, storage
    resources = load_defaults()

    # Create your agent
    agent = Agent(resources=resources)

    # Start chatting!
    await agent.chat("")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run It!
```bash
python hello_agent.py
```

**What just happened?** You created a production-ready AI agent with:
- 🧠 **Intelligent responses** from local or cloud LLM
- 💾 **Persistent memory** that remembers conversations
- 📊 **Automatic logging** for monitoring and debugging
- 🔧 **Zero configuration** - it just works!

**⏰ Time check: 2 minutes** ✅

---

## 🎭 **Minute 3: Adding Personality**

Let's give your agent a specific role and personality using Entity's configuration system:

### `tutor_config.yaml`
```yaml
# Python Tutor Agent Configuration
role: |
  You are an expert Python tutor with 10 years of teaching experience.

  Your personality:
  - Patient and encouraging with beginners
  - Enthusiastic about Python's elegance and power
  - Always provide practical, runnable examples
  - Explain concepts step-by-step with clear reasoning

  Your teaching style:
  - Start with simple explanations, then add complexity
  - Always include code examples with comments
  - Be encouraging and positive about learning

resources:
  llm:
    temperature: 0.3  # More consistent educational responses
    max_tokens: 2000  # Allow for detailed explanations
```

### `tutor_agent.py`
```python
import asyncio
from entity import Agent

async def main():
    # Load agent with custom personality
    agent = Agent.from_config("tutor_config.yaml")

    print("🐍 Python Tutor Agent loaded!")
    print("Ask me about Python concepts, and I'll teach you step-by-step!")

    await agent.chat("")

if __name__ == "__main__":
    asyncio.run(main())
```

### Try It!
```bash
python tutor_agent.py
# Ask: "Explain Python decorators"
```

**What's different?** Your agent now has:
- 🎭 **Specific personality** and expertise
- 🎯 **Focused behavior** as a Python tutor
- ⚙️ **Configuration-driven** customization (no code changes!)

**⏰ Time check: 3 minutes** ✅

---

## 🔧 **Minute 4: Superpowers with Tools**

Let's give your agent real-world capabilities with Entity's built-in tools:

### `superagent_config.yaml`
```yaml
# Super-powered agent with tools
role: |
  You are a helpful AI assistant with access to powerful tools.

  Your approach:
  - Use web search for current information
  - Use calculator for mathematical operations
  - Use file operations when users mention files
  - Explain what tools you're using and why

# Enable built-in tools
tools:
  web_search:
    enabled: true
    max_results: 5

  calculator:
    enabled: true
    precision: 10

  file_operations:
    enabled: true
    read_only: false
    max_file_size_mb: 10

resources:
  llm:
    temperature: 0.1  # Lower for tool usage accuracy
    max_tokens: 3000
```

### `super_agent.py`
```python
import asyncio
from entity import Agent

async def main():
    agent = Agent.from_config("superagent_config.yaml")

    print("🦸‍♀️ Super Agent loaded with tools:")
    print("🌐 Web Search - Find current information")
    print("🧮 Calculator - Perform complex calculations")
    print("📁 File Operations - Read and write files")

    await agent.chat("")

if __name__ == "__main__":
    asyncio.run(main())
```

### Test the Powers!
```bash
python super_agent.py
# Try: "Search for Python 3.12 features and calculate 15% of 200"
# Try: "Create a file called test.txt with a Python example"
```

**Amazing!** Your agent can now:
- 🌐 **Search the web** for current information
- 🧮 **Perform calculations** with perfect accuracy
- 📁 **Work with files** safely and intelligently
- 🔗 **Chain tools** together for complex tasks

**⏰ Time check: 4 minutes** ✅

---

## 🎉 **Minute 5: Exploring What You Built**

Congratulations! In just 4 minutes, you've built increasingly sophisticated AI agents. Let's explore what makes this special:

### What You've Accomplished

1. **🤖 Basic Agent**: Zero-config intelligent assistant
2. **🎭 Personality Agent**: Custom role and behavior via YAML
3. **🦸‍♀️ Super Agent**: Multi-tool capabilities for real-world tasks

### The Entity Advantage

**Traditional AI Development:**
```python
# Hundreds of lines of boilerplate code:
# - LLM client setup and error handling
# - Memory management and persistence
# - Tool integration and safety
# - Configuration and environment handling
# - Logging and monitoring setup
# - User interface and interaction loops
```

**Entity Framework:**
```python
# Just the essentials:
agent = Agent.from_config("config.yaml")
await agent.chat("")  # Everything else handled automatically
```

### Key Entity Concepts You've Learned

✅ **Zero Configuration**: `load_defaults()` sets up everything automatically
✅ **Configuration-Driven**: YAML files control behavior without code changes
✅ **Tool Integration**: Built-in tools extend capabilities instantly
✅ **Plugin Architecture**: Modular, testable, reusable components
✅ **Production Ready**: Logging, monitoring, and safety built-in

**⏰ Final time check: 5 minutes** 🎉

---

## 🚀 **What's Next?**

You've mastered the basics! Here's your learning path:

### 📚 **Continue Learning (10 minutes each)**
- **[Agent Personalities](../examples/02_agent_personality/)** - Deep dive into customization
- **[Tool Usage](../examples/03_tool_usage/)** - Master the tool system
- **[Memory Systems](../examples/04_conversation_memory/)** - Build agents that remember
- **[Streaming Responses](../examples/05_streaming_responses/)** - Real-time interactions

### 🎯 **Real-World Projects (30-60 minutes each)**
- **[Customer Service Bot](../examples/customer_service/)** - Business application
- **[Research Assistant](../examples/research_assistant/)** - Complex workflows
- **[Code Reviewer](../examples/code_reviewer/)** - Developer tools

### 🏗️ **Production Development (2+ hours)**
- **[Multi-Agent Systems](../examples/multi_agent/)** - Orchestrated collaboration
- **[API Integration](../examples/api_service/)** - FastAPI + Entity
- **[Production Deployment](../examples/production/)** - Scalable systems

### 🎓 **Advanced Topics**
- **[Custom Plugin Development](docs/plugins.md)** - Extend Entity framework
- **[Performance Optimization](docs/performance.md)** - Scale to production
- **[Contributing Guide](CONTRIBUTING.md)** - Join the community

---

## 🔧 **Troubleshooting**

### Common Issues

**"No LLM available" Error**
```bash
# Install Ollama (recommended)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama serve

# Or set API key
export OPENAI_API_KEY="your-key"
```

**"Permission denied" or Port Issues**
```bash
# Check for port conflicts
lsof -i :11434  # Ollama port

# Restart Ollama if needed
pkill ollama
ollama serve
```

**Import Errors**
```bash
# Ensure Entity is installed correctly
pip install --upgrade entity-core

# Verify installation
python -c "import entity; print('Entity installed successfully!')"
```

### Get Help

- 💬 **[Discord Community](https://discord.gg/entity)** - Real-time help
- 📚 **[Documentation](https://entity-core.readthedocs.io/)** - Complete guides
- 🐛 **[GitHub Issues](https://github.com/Ladvien/entity/issues)** - Bug reports
- 💡 **[Discussions](https://github.com/Ladvien/entity/discussions)** - Q&A and ideas

---

## 🎯 **Success!**

**You've just experienced the Entity advantage:**

- ⚡ **10x faster development** - Minutes instead of hours
- 🔧 **Zero boilerplate** - Focus on your agent's purpose, not infrastructure
- 🏗️ **Plugin architecture** - Modular, testable, maintainable
- 🚀 **Production ready** - Built-in safety, monitoring, and scaling

**Ready to build the future of AI?** Your Entity journey starts now! 🚀

---

<div align="center">

**What will you build next?**

[📚 Explore Examples](../examples/) •
[🔧 Build Custom Tools](docs/tools.md) •
[🤝 Join Community](https://discord.gg/entity)

**Entity Framework**: *Build better AI agents, faster.* ✨

</div>
