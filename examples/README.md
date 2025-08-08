# Entity Framework Examples

This directory contains examples demonstrating the **proper way** to build applications using Entity framework's plugin-based architecture.

## 🏗️ Entity Framework Architecture

Entity follows a **plugin-based architecture** with a **6-stage workflow**:

```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

### The Right Way: Plugin-Based Design

✅ **Examples that demonstrate proper Entity usage:**

- **`simple_chat/`** - Basic conversational agent using custom plugins
- **`code_reviewer/`** - Code analysis agent with specialized input processing
- **`research_assistant/`** - Multi-modal research with complex plugin pipeline
- **`default_agent.py`** - Minimal example using Entity's default plugins

### Key Principles

1. **Inherit from Entity Plugin Classes**
   ```python
   from entity.plugins.input_adapter import InputAdapterPlugin
   from entity.plugins.prompt import PromptPlugin
   from entity.plugins.output_adapter import OutputAdapterPlugin

   class MyInputPlugin(InputAdapterPlugin):
       # Custom input processing logic
   ```

2. **Define Workflows in YAML**
   ```yaml
   input:
     - my_app.plugins.MyInputPlugin:
         config_param: value

   think:
     - my_app.plugins.MyReasoningPlugin:
         llm_model: "gpt-4"

   output:
     - my_app.plugins.MyOutputPlugin:
         format: "markdown"
   ```

3. **Use Agent.from_config() Pattern**
   ```python
   agent = Agent.from_config("workflow_config.yaml")
   await agent.chat("")  # Uses plugin pipeline
   ```

4. **Inter-Plugin Communication via Context**
   ```python
   # In one plugin
   await context.remember("extracted_data", data)

   # In another plugin
   data = await context.recall("extracted_data", default={})
   ```

## ❌ Anti-Patterns: What NOT to Do

**Avoid these common mistakes when building with Entity framework:**

```python
# ❌ DON'T: Direct Agent.chat() bypassing plugins
agent = Agent(resources=resources)
await agent.chat("Direct message")  # Bypasses workflow stages

# ❌ DON'T: Manual CLI argument parsing
import argparse
parser = argparse.ArgumentParser()  # Use Entity's ArgumentParsingResource instead

# ❌ DON'T: Create agents without configuration
agent = Agent()  # Missing resource configuration

# ❌ DON'T: Skip plugin inheritance
class MyThing:  # Should inherit from Plugin base classes
    pass
```

**✅ DO: Use Entity's plugin architecture**

```python
# ✅ DO: Plugin-based workflows
class MyInputPlugin(InputAdapterPlugin):
    async def _execute_impl(self, context):
        # Process input following Entity patterns

agent = Agent.from_config("workflow.yaml")
await agent.chat("")  # Uses configured plugin pipeline
```

## 🚀 Getting Started

### Prerequisites
```bash
# Install Entity Core
pip install entity-core

# Or use uv (recommended)
uv add entity-core
```

### Running Examples

1. **Start with the simplest example**:
```bash
cd examples
python default_agent.py
```

2. **Try plugin-based examples**:
```bash
# Simple chat with custom plugins
cd simple_chat
python simple_chat.py

# Code review with file processing
cd code_reviewer
python code_reviewer.py
```

3. **Configure your environment**:
```bash
# Set up your LLM provider
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
```

## 📚 Learning Path

### For Beginners
1. **[default_agent.py](./default_agent.py)** - Minimal Entity usage with defaults
2. **[simple_chat/](./simple_chat/)** - Basic plugin inheritance patterns
3. **[code_reviewer/](./code_reviewer/)** - File processing and validation

### For Plugin Developers
1. Study the **plugin base classes** in Entity core
2. Examine **YAML configuration patterns** in examples
3. Learn **context.remember/recall** for inter-plugin communication

### For Framework Contributors
1. Understand the **6-stage workflow** design
2. Master **resource management** patterns
3. Build **custom resources** following Entity conventions

## 🛠️ Common Patterns

### Plugin Development
```python
from entity.plugins.input_adapter import InputAdapterPlugin
from entity.workflow.executor import WorkflowExecutor

class MyInputPlugin(InputAdapterPlugin):
    supported_stages = [WorkflowExecutor.INPUT]

    async def _execute_impl(self, context):
        # Process user input
        user_message = context.message
        processed_data = await self.process_input(user_message)
        await context.remember("processed_input", processed_data)
        return processed_data
```

### Workflow Configuration
```yaml
input:
  - my_agent.plugins.input_plugins.MyInputPlugin:
      config_param: value

think:
  - my_agent.plugins.thinking_plugins.MyReasoningPlugin:
      model: "gpt-4"
      temperature: 0.1

output:
  - my_agent.plugins.output_plugins.MyOutputPlugin:
      format: "markdown"
```

### Resource Access
```python
async def _execute_impl(self, context):
    # Access core resources
    llm = context.get_resource("llm")
    memory = context.get_resource("memory")
    logger = context.get_resource("logging")

    # Use resources in plugin logic
    result = await llm.generate("Your prompt")
    await logger.log(LogLevel.INFO, LogCategory.PLUGIN_LIFECYCLE, "Processing complete")
```

## 📊 Performance Tips

1. **Use context.remember/recall**: Share data efficiently between plugins
2. **Configure appropriate models**: Balance quality vs. speed for your use case
3. **Implement proper error handling**: Use Entity's logging resource
4. **Validate configurations**: Use Pydantic models for plugin config
5. **Follow Entity patterns**: Inherit from base classes, use supported_stages

## 🤝 Contributing

To add a new plugin-based example:

1. Create a directory: `examples/your_agent/`
2. Include:
   - `your_agent.py` - Main entry point using Agent.from_config()
   - `config.yaml` - Workflow configuration
   - `plugins/` - Custom plugin implementations
   - `README.md` - Usage instructions
3. Follow Entity's plugin architecture patterns
4. Test with the 6-stage workflow
5. Submit a pull request

## 🔗 Entity Framework Resources

- **Entity Core Documentation**: Check the source code for the latest patterns
- **Plugin Base Classes**: `entity.plugins.input_adapter`, `entity.plugins.prompt`, `entity.plugins.output_adapter`
- **Workflow Configuration**: YAML-based stage definitions
- **Resource System**: Core resources like LLM, Memory, Logging, FileStorage

**Build powerful AI agents with Entity's plugin architecture!** 🚀
