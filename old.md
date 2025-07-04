# Entity Pipeline Framework Architecture Summary

## 🎯 Vision
A **pipeline-based plugin framework** for AI agents that processes requests through configurable stages, inspired by Bevy's plugin architecture. **Progressive disclosure design**: dead simple for beginners, infinitely powerful for experts.

**Requires Python 3.11 or higher.**

## 🚀 The 15-Minute Experience (Layer 1: Dead Simple)

### Getting Started - Zero Config
```python
from entity import Agent

# Create an agent in one line
agent = Agent()

# Add functionality with decorators
@agent.plugin
def hello(context):
    return f"Hello {context.user}! How can I help?"

@agent.plugin  
def weather(context):
    if "weather" in context.message:
        return "It's sunny and 72°F today!"

@agent.plugin
def calculator(context):
    if "calculate" in context.message:
        # Built-in tools available automatically
        result = context.calculate("2 + 2")
        return f"The answer is {result}"

# Run the agent
agent.run_http()  # Automatically starts server on localhost:8000
```

The default setup registers a simple `CalculatorTool`, a `SearchTool`, and a
`UnifiedLLMResource` using the `echo` provider, so the example above works
without any configuration files.

```python
from entity.tools import SearchTool

# Add web search capability
agent.tool_registry.add("search", SearchTool())

@agent.plugin
async def lookup(context):
    result = await context.use_tool("search", query="Entity Pipeline")
    return result
```

### Running the Examples
The example scripts in the `examples` folder can be executed directly from the
repository root. Each script adjusts `sys.path` so the `src` directory is
discoverable:

```bash
python examples/servers/http_server.py
python examples/pipelines/pipeline_example.py
```

### Command Line Usage
Launch an agent from a YAML configuration file. Example configurations are
provided in `config/dev.yaml` and `config/prod.yaml`:

```bash
python src/cli.py --config config/dev.yaml
```

### One-Liner Context Operations
```python
@agent.plugin
def smart_assistant(context):
    # Dead simple context operations
    context.think("Let me analyze this request...")      # Internal reasoning
    context.say("I'm working on that...")                # User-visible response
    
    weather = context.use_tool("weather", city="SF")     # Returns result directly
    context.remember("user_location", "San Francisco")   # Auto-persistence
    
    # Conversation helpers
    if context.is_question():
        return context.ask_llm("Please answer: " + context.message)
    
    return "I understand!"
```

### Instant Plugin Discovery
The pipeline automatically registers plugin classes placed under
`plugins`. Simply create a new plugin class that inherits from the
appropriate base class and it becomes available when the agent loads.

```python
# Framework auto-discovers plugins by naming convention
# functions must end with `_plugin`
# weather_plugin.py
def weather_plugin(context):
    return get_weather_data()

# calculator_plugin.py  
def calculator_plugin(context):
    return calculate_math(context.message)

# Just drop files in plugins/ folder - they work automatically
agent = Agent.from_directory("./plugins")  # Auto-loads everything
# Import errors are logged and remaining plugins still load
from pipeline import PromptPlugin, PipelineStage

class MyCustomPrompt(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return "Hello from my plugin"

agent = Agent.from_package("plugins")
agent.run_http()
```

### Multi-Turn and Complex Reasoning Patterns

The framework supports complex reasoning and multi-turn scenarios through explicit mechanisms:

#### **Plugin-Level Iteration for Complex Reasoning**
```python
class ReActPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    
    async def _execute_impl(self, context: PluginContext):
        max_steps = self.config.get("max_steps", 5)
        
        # Internal plugin iteration - no pipeline loops needed
        for step in range(max_steps):
            # Think
            thought = await self.call_llm(context, thought_prompt, purpose=f"react_thought_{step}")
            
            # Act (execute tools immediately)
            if self._should_take_action(thought.content):
                action_name, params = self._parse_action_from_thought(thought.content)
                result_key = context.execute_tool(action_name, params)
                # Tool result immediately available
            
            # Decide if done
            if self._should_conclude(thought.content):
                context.set_response(self._extract_final_answer(thought.content))
                return
        
        context.set_response("Reached reasoning limit without conclusion.")
```

#### **Explicit Pipeline Delegation for Multi-Step Workflows**
```python
class MultiStepWorkflowPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext):
        if self._needs_more_processing(context):
            # Explicitly delegate back to pipeline for another pass
            context.set_response({
                "type": "continue_processing",
                "message": "I need to search for more information about X",
                "internal": True,
                "workflow_state": {"step": 2, "data": "..."}
            })

# Agent-level conversation management
class ConversationManager:
    async def process_request(self, user_message: str) -> str:
        response = await execute_pipeline(user_message)
        
        # Handle multi-step workflows
        while response.get("type") == "continue_processing":
            follow_up = response["message"]
            response = await execute_pipeline(follow_up)
        
        return response
```

#### **Multi-Turn Conversations (Application Level)**
```python
# Each user message triggers one pipeline execution
conversation_history = []

for user_message in conversation:
    # Add conversation history to context
    enhanced_request = {
        "message": user_message,
        "history": conversation_history[-10:]  # Last 10 messages
    }
    
    response = await execute_pipeline(enhanced_request)
    conversation_history.append({"user": user_message, "assistant": response})
```

The framework maintains its sophisticated five-stage pipeline underneath the simple interface, automatically routing simple plugins to appropriate stages.


## Legacy Architecture Notes
The remainder of this document duplicated the information now maintained in [ARCHITECTURE.md](ARCHITECTURE.md). Refer there for full details.
