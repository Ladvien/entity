# Examples & Tutorials

Entity Framework comes with a comprehensive set of examples that demonstrate the framework's capabilities and teach you to build increasingly sophisticated AI agents.

## 🚀 Quick Start Tutorial

For a complete guided experience, start with our [5-Minute Quick Start Tutorial](quickstart.md) that takes you from installation to a working agent with tools and memory.

## 📚 Example Suite

Our examples are designed to teach Entity Framework concepts progressively:

### 1. Hello Agent - Zero Configuration
**Location**: [examples/01_hello_agent/](../examples/01_hello_agent/)

Your first Entity agent with absolutely zero configuration required. Demonstrates:
- Automatic LLM setup (local Ollama or cloud APIs)
- Built-in memory that persists between conversations
- Interactive chat interface

Perfect for: First-time users who want to see Entity in action immediately.

### 2. Agent Personality - YAML Configuration
**Location**: [examples/02_agent_personality/](../examples/02_agent_personality/)

Learn to customize your agent's role and behavior through configuration files. Demonstrates:
- Role-based agents with specific personalities
- YAML configuration for behavior customization
- Communication styles (professional, educational, casual)
- Domain expertise specialization

Perfect for: Building specialized agents for specific domains or use cases.

### 3. Tool Usage - Superpower Your Agent
**Location**: [examples/03_tool_usage/](../examples/03_tool_usage/)

Give your agent real-world capabilities with Entity's powerful tool system. Demonstrates:
- Web search integration
- Calculator and mathematical operations
- File operations and data processing
- Tool chaining for complex workflows

Perfect for: Creating agents that can interact with external systems and data.

### 4. Conversation Memory - Agents That Remember
**Location**: [examples/04_conversation_memory/](../examples/04_conversation_memory/)

Build agents that maintain context and learn user preferences over time. Demonstrates:
- Persistent memory across sessions
- User preference tracking and personalization
- Context-aware conversations
- Long-term relationship building

Perfect for: Customer service, tutoring, and personal assistant applications.

### 5. Streaming Responses - Real-Time Interactions
**Location**: [examples/05_streaming_responses/](../examples/05_streaming_responses/)

Create responsive, interactive experiences with real-time streaming. Demonstrates:
- Token-by-token response streaming
- Progress indicators and status updates
- Interactive user experiences
- Optimized performance patterns

Perfect for: Web applications and real-time chat interfaces.

## 🎯 Framework Showcase

For a comprehensive demonstration of all Entity Framework features:

**Location**: [examples/framework_showcase/](../examples/framework_showcase/)

This example combines all Entity capabilities into a single, powerful demonstration including:
- Plugin architecture with inheritance patterns
- YAML-driven configuration
- Zero-config defaults
- Tool integration
- Memory and personality systems
- Production-ready patterns

## 🔧 Example Structure

Each example follows a consistent structure:
- `README.md` - Comprehensive explanation and learning guide
- `*.py` - Runnable Python code with detailed comments
- `*.yaml` - Configuration files showing YAML-driven development
- `requirements.txt` - Dependencies for easy setup

## 🏃‍♂️ Running the Examples

```bash
# Navigate to any example
cd examples/01_hello_agent

# Install dependencies
pip install -r requirements.txt

# Run the example
python hello_agent.py
```

## 🎓 Learning Path

We recommend following this progression:

1. **Start with Hello Agent** - Get Entity running in 30 seconds
2. **Try Agent Personality** - Learn configuration-driven development
3. **Explore Tool Usage** - See real-world capabilities
4. **Test Conversation Memory** - Experience long-term interactions
5. **Experiment with Streaming** - Build responsive interfaces
6. **Study Framework Showcase** - See everything working together

Each example builds on concepts from previous ones while introducing new capabilities. By the end, you'll understand Entity's revolutionary approach to AI agent development!

## 💡 Next Steps

After working through the examples:
- Explore the [API Reference](api/modules.rst) for detailed technical documentation
- Check out [Architecture](architecture.md) for deeper understanding of Entity's design
- Read our [Contributing Guide](contributing.md) to join the community
