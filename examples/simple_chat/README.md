# Simple Chat Agent

This example demonstrates the **proper way** to build Entity framework applications using the plugin architecture.

## What This Example Shows

### ✅ Proper Entity Architecture

- **Plugin Inheritance**: Custom plugins inherit from Entity base classes
  - `ChatInputPlugin` extends `InputAdapterPlugin`
  - `ChatReasoningPlugin` extends `PromptPlugin`
  - `ChatOutputPlugin` extends `OutputAdapterPlugin`

- **6-Stage Workflow**: Uses Entity's standard pipeline
  - **INPUT**: Process user input and maintain conversation history
  - **PARSE**: (skipped for simple chat)
  - **THINK**: Analyze context and generate responses using LLM
  - **DO**: (skipped for simple chat)
  - **REVIEW**: (skipped for simple chat)
  - **OUTPUT**: Format responses and update conversation history

- **YAML Configuration**: Workflow defined declaratively in `chat_config.yaml`
- **Resource Dependencies**: Plugins declare dependencies (e.g., `llm`)
- **Configuration Validation**: Uses Pydantic models for plugin config
- **Inter-Plugin Communication**: Uses `context.remember()` and `context.recall()`

### 🔧 Plugin Architecture Benefits

1. **Modularity**: Each plugin has a single responsibility
2. **Reusability**: Plugins can be mixed and matched across agents
3. **Configurability**: Behavior controlled via YAML configuration
4. **Testability**: Individual plugins can be unit tested
5. **Extensibility**: New functionality added by creating new plugins

## Project Structure

```
simple_chat/
├── chat_agent.py           # Main application entry point
├── chat_config.yaml        # Workflow and plugin configuration
├── plugins/
│   ├── __init__.py
│   ├── input_plugins.py    # INPUT stage plugins
│   ├── thinking_plugins.py # THINK stage plugins
│   └── output_plugins.py   # OUTPUT stage plugins
└── README.md
```

## How It Works

1. **Agent Creation**: `Agent.from_config()` loads the YAML configuration
2. **Plugin Instantiation**: Entity instantiates plugins with resources and config
3. **Workflow Execution**: Agent processes messages through the 6-stage pipeline
4. **Plugin Communication**: Plugins share data via the context object

## Key Plugins

### ChatInputPlugin (INPUT)
- Processes user input
- Manages conversation history
- Handles system commands (`/help`, `/clear`, `/status`)

### ChatReasoningPlugin (THINK)
- Uses LLM to generate contextual responses
- Considers conversation history
- Configurable personality and response style

### ChatOutputPlugin (OUTPUT)
- Formats responses for delivery
- Updates conversation history with assistant responses
- Supports multiple output formats

## Configuration

The `chat_config.yaml` file demonstrates Entity's configuration system:

```yaml
input:
  - simple_chat.plugins.input_plugins.ChatInputPlugin:
      max_history_length: 50
      enable_system_commands: true

think:
  - simple_chat.plugins.thinking_plugins.ChatReasoningPlugin:
      personality: "helpful and friendly"
      response_style: "conversational"

output:
  - simple_chat.plugins.output_plugins.ChatOutputPlugin:
      format_style: "plain"
      add_to_history: true
```

## Running the Example

```bash
# From the project root
cd examples/simple_chat
python chat_agent.py
```

## Contrast with Anti-Patterns

❌ **Wrong Way** (what the original examples were doing):
- Manual CLI parsing with argparse
- Direct Agent.chat() calls without plugins
- Bypassing the workflow system entirely
- No reusable components

✅ **Right Way** (this example):
- Plugin-based architecture following Entity patterns
- YAML-configured workflows
- Proper resource management
- Framework-idiomatic design

This example shows how Entity framework is meant to be used: as a plugin-based system where domain logic is implemented in reusable plugins that participate in the standard 6-stage workflow.
