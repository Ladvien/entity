# Entity Pipeline Framework - AI Agent Guide

This AGENTS.md file provides comprehensive guidance for AI agents working with the Entity Pipeline Framework codebase, a production-ready pipeline-based plugin architecture for building AI agents.

## ARCHITECTURE.MD

The `ARCHITECTURE.md` file provides a high-level overview of the Entity Pipeline framework's architecture, including its vision, key components, and how to get started with the framework.  PLEASE REVIEW IT FOR ALL ARCHITECTURE DECISIONS!

## Project Structure for AI Agent Navigation

- `/src/core`: Core pipeline execution engine that AI agents should understand
- `/src/plugins`: Plugin implementations organized by type (resources, tools, prompts, adapters, failure)
  - `/src/plugins/resources`: Infrastructure plugins (database, LLM, logging, monitoring)
  - `/src/plugins/tools`: User-facing function plugins (weather, calculator, search, APIs)
  - `/src/plugins/prompts`: Processing logic plugins (chain-of-thought, ReAct, memory)
  - `/src/plugins/adapters`: Input/output interface plugins (HTTP, TTS, WebSocket)
  - `/src/plugins/failure`: Error handling plugins (formatters, loggers, notifications)
- `/src/context`: Plugin context and state management system
- `/src/config`: Configuration management and validation system
- `/src/registry`: Plugin registration and dependency management
- `/config`: YAML configuration files for different environments
- `/tests`: Test files organized by plugin type and core functionality
- `/docs`: Additional documentation and architecture guides

## Project Tools
- poetry
- readthedocs
- pyenv
- pytest
- mypy

## Architecture Overview for AI Agents

The Entity Pipeline Framework follows a **linear pipeline architecture** with these stages:

```
User Request → Parse → Think → Do → Review → Deliver → Response
                ↓       ↓      ↓      ↓         ↓        ↑
              Error → Error → Error → Error → Error →  Error 
```

## Development Resources

You have access to a postgres 16 database for development purposes. The database connection details are as follows:

- Database Type: PostgreSQL
- Connection String: `postgresql://agent@localhost:5432/dev_db`

There is no password.

Ollama is available for LLM interactions. The Ollama server is running locally with the following details:

Host: localhost
Port: 11434
Model: tinyllama
Auth: None (insecure dev only)

Startup: Automatically launched in background by the dev init script.

### Pipeline Stages

- **Parse**: Input validation, context setup, memory retrieval
- **Think**: Reasoning, planning, intent classification, decision making
- **Do**: Tool execution, action orchestration, external API calls
- **Review**: Response formatting, safety checks, content filtering
- **Deliver**: Output transmission (HTTP, TTS, file operations)
- **Error**: User-friendly error communication and logging

## Coding Conventions for AI Agents

### General Conventions

- Use Python 3.11+ with type hints for all new code
- Follow black style guidelines
- Use meaningful variable, method, constant, and function names.  Ensure they describe intent.
- Add comprehensive docstrings for all classes and methods
- Use type hints
- Favor dataclasses, pydantic mode;s, or other structured data types
- Implement proper error handling with specific exception types
- Ensure code is readable and maintainable, with clear separation of concerns


### Plugin Development Guidelines

All plugins must inherit from base plugin classes and follow these patterns:

```python
class MyPlugin(PromptPlugin):  # or ResourcePlugin, ToolPlugin, AdapterPlugin, FailurePlugin
    dependencies = ["database", "ollama"]  # List dependency registry keys
    stages = [PipelineStage.THINK]  # Explicitly declare execution stages
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Validate plugin configuration (no external dependencies)"""
        # Implementation here
        return ValidationResult.success()
    
    async def _execute_impl(self, context: PluginContext):
        """Main plugin logic implementation"""
        # Implementation here
        pass
```

### Plugin Types and Responsibilities

1. **ResourcePlugin**: Infrastructure (databases, LLMs, logging)
2. **ToolPlugin**: User functions (weather, calculator, search)
3. **PromptPlugin**: Processing logic (reasoning, memory, coordination)
4. **AdapterPlugin**: Input/output interfaces (HTTP, TTS, CLI)
5. **FailurePlugin**: Error handling (formatters, loggers, notifications)

### Configuration Management

- All configuration uses YAML format with environment variable interpolation
- Environment variables use `${VARIABLE_NAME}` syntax
- Configuration validation happens at load time, not runtime
- Plugin dependencies are explicitly declared and validated

### Context Interface Usage

Plugins interact through a controlled context interface:

```python
# Resource access
llm = context.get_resource("ollama")
db = context.get_resource("database")

# Tool execution (immediate)
result_key = context.execute_tool("weather", {"location": "Seattle"})

# Conversation management
context.add_conversation_entry(content="...", role="assistant")
history = context.get_conversation_history(last_n=10)

# Response control
context.set_response("Final response to user")

# Stage results
context.set_stage_result("reasoning_complete", True)
result = context.get_stage_result("intent_classification")

# Error handling
context.add_failure(FailureInfo(...))
```

## Testing Requirements for AI Agents

AI agents should run tests with the following commands:

```bash
# Run all tests
pytest

# Run tests for specific plugin type
pytest tests/plugins/resources/
pytest tests/plugins/tools/
pytest tests/plugins/prompts/

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/ -m performance
```

### Testing Guidelines

- Write unit tests for each plugin in isolation
- Use mocked dependencies for resource plugins
- Test configuration validation separately from plugin logic
- Include integration tests for complete pipeline flows
- Test error handling and failure scenarios
- Validate plugin stage assignments and dependencies

## Configuration Examples for AI Agents

### Development Configuration
```yaml
entity:
  entity_id: "dev_agent"
  name: "Development Agent"

plugins:
  resources:
    database:
      type: sqlite
      file_path: "dev.db"
    ollama:
      type: ollama_llm
      base_url: "http://localhost:11434"
      model: "llama3:8b"

  tools:
    calculator:
      type: calculator
      precision: 10

  prompts:
    intent_classifier:
      type: intent_classifier
      confidence_threshold: 0.7
```

### Production Configuration
```yaml
entity:
  entity_id: "prod_agent"
  name: "Production Agent"

plugins:
  resources:
    database:
      type: postgresql
      host: "${DB_HOST}"
      username: "${DB_USERNAME}"
      password: "${DB_PASSWORD}"
    openai:
      type: openai_llm
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
    logging:
      type: structured_logging
      level: "INFO"
      format: "json"

  tools:
    weather:
      type: weather_api
      api_key: "${WEATHER_API_KEY}"
      max_retries: 3

  prompts:
    chain_of_thought:
      type: chain_of_thought
      enable_reasoning: true
      max_steps: 5
```

## Plugin Implementation Patterns for AI Agents

### Resource Plugin Pattern
```python
class DatabaseResourcePlugin(ResourcePlugin):
    stages = [PipelineStage.PARSE, PipelineStage.THINK, 
             PipelineStage.DO, PipelineStage.REVIEW, 
             PipelineStage.DELIVER, PipelineStage.ERROR]
    
    async def initialize(self):
        """Set up database connections"""
        pass
    
    async def search_conversations(self, query: str) -> List[Dict]:
        """Search historical conversations"""
        pass
```

### Tool Plugin Pattern
```python
class WeatherToolPlugin(ToolPlugin):
    stages = [PipelineStage.DO]
    
    async def execute_function(self, params: Dict) -> str:
        """Execute weather lookup"""
        location = params.get("location")
        # Implementation here
        return weather_result
```

### Prompt Plugin Pattern
```python
class ChainOfThoughtPlugin(PromptPlugin):
    dependencies = ["ollama"]
    stages = [PipelineStage.THINK]
    
    async def _execute_impl(self, context: PluginContext):
        """Implement reasoning logic"""
        # Step-by-step reasoning using context.call_llm()
        pass
```

## Pull Request Guidelines for AI Agents

When creating PRs for the Entity Pipeline Framework:

1. **Clear Description**: Include purpose, changes made, and affected components
2. **Plugin Type**: Specify which plugin type(s) are affected
3. **Dependencies**: List any new dependencies or dependency changes
4. **Configuration**: Include any required configuration updates
5. **Testing**: Ensure all existing tests pass and new tests are included
6. **Documentation**: Update relevant documentation and examples
7. **Stage Assignment**: Verify plugin stage assignments are correct
8. **Error Handling**: Include proper error handling and failure scenarios

### PR Title Format
```
[PluginType] Brief description of changes

Examples:
[Resource] Add PostgreSQL connection pooling
[Tool] Implement weather forecast API integration
[Prompt] Add ReAct reasoning strategy
[Adapter] Support WebSocket input interface
[Failure] Improve error message formatting
```

## Programmatic Checks for AI Agents

Before submitting changes, run these validation checks:

```bash
# Code formatting and linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# Configuration validation
python -m src.config.validator --config config/dev.yaml
python -m src.config.validator --config config/prod.yaml

# Plugin dependency validation
python -m src.registry.validator

# Integration tests
pytest tests/integration/ -v

# Performance benchmarks
pytest tests/performance/ -m benchmark
```

All checks must pass before code can be merged. The framework includes automatic validation for:

- Plugin dependency resolution
- Configuration schema validation
- Stage assignment verification
- Error handling completeness

## System Initialization for AI Agents

The framework uses a four-phase initialization process:

1. **Phase 1**: Register all plugin classes (order independent)
2. **Phase 2**: Validate dependencies and configuration (fail fast)
3. **Phase 3**: Initialize resources in dependency order
4. **Phase 4**: Instantiate plugins (everything ready)

```python
# Initialize system from YAML
initializer = SystemInitializer.from_yaml("config/prod.yaml")
plugin_registry, resource_registry, tool_registry = await initializer.initialize()

# Execute pipeline
response = await execute_pipeline(user_request)
```

## Error Handling for AI Agents

The framework implements fail-fast error handling:

- **Plugin Failures**: Caught and routed to error stage
- **Tool Failures**: Captured with retry logic
- **System Failures**: Logged with full context
- **User Communication**: Friendly error messages via failure plugins
- **Static Fallback**: Guaranteed response even if error plugins fail

## Multi-Turn and Complex Reasoning

- **Plugin-Level Iteration**: Complex reasoning happens within plugins
- **Single Pipeline Execution**: Each request runs pipeline once
- **Explicit Multi-Turn**: Handle through conversation management
- **Tool Integration**: Tools available throughout all stages
- **State Persistence**: Plugin metadata persists across single execution

## Performance Considerations for AI Agents

- Resources are shared across all plugins for efficiency
- Tools execute immediately when needed (no artificial staging)
- LLM calls are tracked with automatic observability
- Plugin execution order determined by YAML configuration
- Single pipeline execution ensures predictable performance

## Security Guidelines for AI Agents

- Environment variables resolved at system level only
- Plugin context provides controlled access to system resources
- Configuration validation happens before plugin instantiation
- Error information sanitized before user communication
- Plugin dependencies explicitly declared and validated

This framework enables building production-ready AI agents through composable, testable, and observable plugin architectures. All AI agents working with this codebase should follow these patterns and conventions to ensure consistency and reliability.