# Entity Framework: Complete Architecture Guide

## Overview

The Entity framework provides a **unified agent architecture** combining a **4-layer resource system** with a **workflow-based processing model**. This enables immediate development through zero-config defaults while supporting seamless progression to production-grade configurations.

## Core Mental Model

### Agent Composition
```
Agent = Resources + Workflow
```

An **Agent** consists of two primary components:
- **Resources**: Shared capabilities (LLM, Memory, Storage) that plugins can access
- **Workflow**: Stage-specific plugin assignments that define the agent's processing behavior and personality

### Agent Personality Through Plugin Composition
Agent personality and capabilities emerge from the specific plugins assigned to each workflow stage:

- **Helpful Assistant**: Friendly reasoning plugins + polite formatters
- **Data Analyst**: Statistical analysis plugins + chart generators
- **Creative Writer**: Imagination plugins + storytelling formatters

## Core Architecture: 4-Layer Resource System + Workflow Pipeline

### Layer Composition with Constructor Injection

```python
# Layer 1: Infrastructure Primitives (concrete technology)
duckdb_infra = DuckDBInfrastructure("./agent_memory.duckdb")
ollama_infra = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
s3_infrastructure = S3Infrastructure(bucket="my-bucket")

# Layer 2: Concrete Resource Implementations (technology-specific logic)
db_resource = DuckDBDatabaseResource(duckdb_infra)
vector_resource = DuckDBVectorStoreResource(duckdb_infra)
llm_resource = OllamaLLMResource(ollama_infra)
storage_resource = S3StorageResource(s3_infrastructure)

# Layer 3: Canonical Agent Resources (unified interfaces)
memory = Memory(db_resource, vector_resource)  # Constructor injection
llm = LLM(llm_resource)
storage = Storage(storage_resource)

# Layer 4: Agent with Workflow (resources + processing pipeline)
agent = Agent(resources=[memory, llm, storage], workflow=my_workflow)
```

**Constructor-Based Dependency Injection** provides immediate validation with no incomplete state:

```python
class Memory(AgentResource):
    def __init__(self, database: DatabaseResource, vector_store: VectorStoreResource):
        self.database = database      # Constructor injection
        self.vector_store = vector_store
        # Immediate validation - no incomplete state

class ReasoningPlugin(PromptPlugin):
    dependencies = ["llm", "memory"]
    supported_stages = [THINK, REVIEW]  # Multi-stage support

    def __init__(self, llm: LLM, memory: Memory, config: Dict | None = None):
        self.llm = llm        # Constructor injection
        self.memory = memory  # Constructor injection
```

### 6-Stage Workflow Pipeline
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

Each stage serves a specific purpose:
- **INPUT**: Receive and initially process user requests
- **PARSE**: Extract and structure important information
- **THINK**: Perform reasoning, planning, and decision-making
- **DO**: Execute actions, tool calls, and external operations
- **REVIEW**: Validate results and ensure response quality
- **OUTPUT**: Format and deliver final responses

## Layer 0: Zero-Config Development Strategy

### Automatic Resource Defaults

Layer 0 acts as intelligent fallbacks that automatically provide working resources when no explicit configuration exists:

```python
# This just works - no config files needed
from entity import Agent

# Create agent with default workflow and resources
agent = Agent()  # Automatically uses Layer 0 defaults

# Automatically uses:
# - Ollama LLM (localhost:11434, llama3.2:3b)
# - DuckDB Memory (./agent_memory.duckdb)
# - LocalFileSystem Storage (./agent_files/)
# - Default workflow with basic plugins per stage

response = await agent.chat("What's 5 * 7?")
```

### Fallback Behavior Rules

1. **No Configuration → Layer 0 Defaults**
```python
agent = Agent()  # Uses Ollama + DuckDB + LocalFileSystem + default workflow
```

2. **Partial Configuration → Selective Override**
```python
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {"type": "openai", "model": "gpt-4"}
            # memory, storage use Layer 0 defaults
        }
    },
    "workflows": {
        "custom": {
            "think": ["advanced_reasoning"]
            # other stages use defaults
        }
    }
})
```

3. **Full Configuration → No Defaults**
```python
# If config.yaml specifies all resources and workflow, no defaults used
agent = Agent.from_config("config.yaml")
```

## Workflow System Implementation

### Default Framework Plugins
The framework provides sensible defaults for all stages:

```yaml
defaults:
  input: [basic_input_adapter]
  parse: [basic_parser]
  think: [basic_reasoning]
  do: [basic_tool_executor]
  review: [basic_validator]
  output: [basic_formatter]
```

### Workflow Templates
Named workflows override defaults as needed:

```yaml
workflows:
  helpful_assistant:
    think: [friendly_reasoning_plugin]
    output: [polite_formatter_plugin]
    # Other stages use framework defaults

  data_analyst:
    parse: [csv_parser_plugin]
    think: [statistical_analysis_plugin]
    output: [chart_generator_plugin]
    # Other stages use framework defaults
```

### Multi-Stage Plugin Support

Plugins can operate in multiple stages with author-defined restrictions:

```python
class ValidationPlugin(PromptPlugin):
    supported_stages = [PARSE, REVIEW]  # Author-defined limitations

class UniversalFormatterPlugin(PromptPlugin):
    supported_stages = [PARSE, THINK, OUTPUT]  # More flexible usage

# Workflow can use same plugin in multiple stages
workflows:
  careful_analyst:
    parse: [validation_plugin]     # ✅ Supported
    review: [validation_plugin]    # ✅ Supported
    think: [validation_plugin]     # ❌ Error - not supported
```

## Configuration Options

### Zero Config (Layer 0 Defaults)
```python
agent = Agent()  # Works immediately with defaults
response = await agent.chat("Hello")
```

### Partial Configuration (Layer 0 + Custom)
```python
# Override just LLM, keep other defaults
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {
                "type": "entity.resources.llm:OpenAILLMResource",
                "api_key": "${OPENAI_API_KEY}",
                "model": "gpt-4"
            }
            # memory, storage automatically use Layer 0 defaults
        }
    },
    "workflows": {
        "my_agent": {
            "think": ["creative_reasoning"],
            "output": ["markdown_formatter"]
        }
    }
})

agent = Agent.from_workflow("my_agent")
# Uses: OpenAI LLM + DuckDB Memory + LocalFileSystem Storage + custom workflow
```

### Full Configuration (Explicit Control)
```yaml
# config.yaml - explicit resource and workflow configuration
plugins:
  resources:
    llm:
      type: entity.resources.llm:OpenAILLMResource
      api_key: ${OPENAI_API_KEY}
      model: gpt-4-turbo

    memory:
      type: entity.resources.memory:PostgresMemory
      host: localhost
      database: production_db

    storage:
      type: entity.resources.storage:S3Storage
      bucket: my-agent-files
      region: us-west-2

workflows:
  production_agent:
    input: [secure_input_handler]
    parse: [enterprise_parser, compliance_checker]
    think: [advanced_reasoning, domain_expertise]
    do: [secure_tool_executor, audit_logger]
    review: [quality_assurance, security_validator]
    output: [professional_formatter, response_logger]
```

```python
# No Layer 0 defaults used - everything explicit
agent = Agent.from_config("config.yaml")
response = await agent.chat("Analyze this...")  # Uses PostgreSQL + S3 + GPT-4 + production workflow
```



No, .env credential interpolation is not in the new architecture document. I see `${OPENAI_API_KEY}` examples but no explanation of the substitution system.

**Add this section after "Configuration Options" and before "Progressive Disclosure Model":**

## Environment Variable Substitution

**Decision**: All plugins/resources implement `config()` method that recursively substitutes `${VAR}` patterns in dictionary values. Uses `${VAR}` syntax only, fails on missing variables, obfuscates credentials in logs, and auto-discovers `.env` with explicit path override.

**Implementation Pattern**:
```python
class BasePlugin:
    @classmethod
    def config(cls, config_dict: Dict[str, Any], env_file: str = None) -> Dict[str, Any]:
        """Recursively substitute ${VAR} in all dictionary values"""
        return substitute_variables(config_dict, env_file)

def substitute_variables(obj: Any, env_file: str = None) -> Any:
    """Recursively substitute ${VAR} patterns with environment values"""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv('.env')  # Auto-discovery

    if isinstance(obj, str):
        def replace_var(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Environment variable ${{{var_name}}} not found")
            return value
        return re.sub(r'\$\{([^}]+)\}', replace_var, obj)
    elif isinstance(obj, dict):
        return {k: substitute_variables(v, env_file) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_variables(item, env_file) for item in obj]
    return obj
```

**Usage Examples**:
```yaml
# config.yaml
plugins:
  resources:
    llm:
      api_key: ${OPENAI_API_KEY}
      model: ${LLM_MODEL}

    database:
      host: ${DB_HOST}
      password: ${DB_PASS}
```

**Security**: Credential values are obfuscated in logs as `api***key` format.




## Progressive Disclosure Model

### Layer 1: Named Workflow Templates
```python
# Pre-built agent types with sensible workflows
agent = Agent.from_workflow("helpful_assistant")
agent = Agent.from_workflow("data_analyst")
agent = Agent.from_workflow("creative_writer")

response = await agent.chat("Hello, how can I help?")
```

### Layer 2: Custom Workflow Definitions
```yaml
# custom_workflow.yaml
workflows:
  my_specialist:
    input: [specialized_input_handler]
    parse: [domain_parser, entity_extractor]
    think: [expert_reasoning, domain_knowledge]
    do: [specialized_tools, external_apis]
    review: [domain_validator, compliance_checker]
    output: [technical_formatter, audit_logger]
```

```python
agent = Agent.from_config("custom_workflow.yaml")
```

## Plugin System Architecture

### Plugin Validation Requirements

Every plugin implements mandatory validation methods called during agent startup:

```python
class BasePlugin:
    supported_stages = [THINK]  # Default stage support

    def validate_config(self) -> ValidationResult:
        """Synchronous validation: config syntax, required fields, dependency declarations"""
        # Creation-time validation - fail fast
        if hasattr(self, 'assigned_stage') and self.assigned_stage not in self.supported_stages:
            return ValidationResult.error(f"Plugin not supported in {self.assigned_stage}")

    async def validate_runtime(self) -> ValidationResult:
        """Asynchronous validation: external connectivity, infrastructure readiness"""

    async def _execute_impl(self, context: PluginContext) -> None:
        # Runtime safety check
        if context.current_stage not in self.supported_stages:
            raise UnsupportedStageError(f"Plugin cannot run in {context.current_stage}")
```

**Validation Strategy**: Both fail-fast at creation time and runtime safety checks ensure system reliability.

### Workflow + Auto-Assignment Coexistence
The system supports both approaches simultaneously:

**Plugin Auto-Assignment**
```python
class ReasoningPlugin(PromptPlugin):
    stage = THINK  # Plugin declares default stage
    supported_stages = [THINK, REVIEW]
```

**Workflow Override**
```yaml
workflows:
  analyst:
    think: [statistical_reasoning]  # Overrides ReasoningPlugin default
    review: [statistical_reasoning] # Same plugin, different stage
    # Other stages use auto-assigned plugins or defaults
```

**Priority Order**: Workflow assignment → Plugin class default → Framework default

## Plugin Context: Dual Interface Pattern

### Anthropomorphic Interface for Simplicity

```python
class BasicPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Simple interface - most common usage

        # Temporary thoughts (cleared after pipeline execution)
        await context.think("analysis", result)        # Store temporary thoughts
        analysis = await context.reflect("analysis")   # Retrieve temporary thoughts

        # Persistent memory (survives across conversations)
        await context.remember("user_prefs", data)     # Persistent storage
        prefs = await context.recall("user_prefs")     # Persistent retrieval

        # Final response
        await context.say("Here's my response")        # Final response
```

### Direct Resource Access for Advanced Operations

```python
class AdvancedPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Advanced interface - complex operations
        memory = context.get_resource("memory")
        results = await memory.query("SELECT * FROM user_prefs WHERE...")
        similar = await memory.vector_search("preferences", k=5)

        # Still can use anthropomorphic interface
        await context.think("search_results", similar)
```

## Plugin Discovery Architecture

**Decision**: Git-based plugin distribution with CLI installation tools. Future registry integration planned as ecosystem grows.

```bash
# Git-based installation
entity-cli plugin install https://github.com/user/weather-plugin
entity-cli plugin install git@company.com:internal/custom-tools

# Plugin manifest (entity-plugin.yaml in repo root)
name: weather-plugin
version: 1.0.0
permissions: [external_api, storage]
dependencies: [requests, aiohttp]
entry_point: weather_plugin.WeatherPlugin
supported_stages: [DO, REVIEW]
```

**Core Features**:
- **Git repositories**: Primary distribution mechanism for public and private plugins
- **Plugin manifests**: Declare permissions, dependencies, and supported stages
- **CLI management**: Install, uninstall, list, and update commands
- **Validation pipeline**: Automatic structure and security validation during install
- **Permission model**: User confirms plugin capabilities before installation
- **Local cache**: Downloaded plugins stored in `~/.entity/plugins/`

**Security Model**:
- Plugin manifests declare required permissions and supported stages
- Install-time validation of plugin structure and dependencies
- User explicit confirmation for permission grants
- Sandboxed execution environment for untrusted plugins

## Error Handling

### Missing Layer 0 Dependencies

```python
# If Ollama not available
agent = Agent()  # Clear error: "Ollama not found. Install: brew install ollama"

# If DuckDB creation fails
agent = Agent()  # Graceful fallback: in-memory storage with warning
```

### Configuration Validation

```python
# Invalid resource config fails fast
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {"type": "invalid_llm"}  # Immediate error
        }
    }
})

# Invalid stage assignment fails fast
agent = Agent.from_config({
    "workflows": {
        "my_workflow": {
            "think": ["invalid_plugin_for_stage"]  # Validation error
        }
    }
})
```

## Implementation Examples

### Basic Usage
```python
# Using pre-built workflow template
agent = Agent.from_workflow("helpful_assistant")
response = await agent.chat("Hello, how are you?")
```

### Advanced Customization
```python
# Custom workflow with specific plugin combinations
custom_workflow = {
    "think": ["analytical_reasoning", "creativity_booster"],
    "output": ["markdown_formatter", "emoji_enhancer"]
}

agent = Agent.from_workflow_dict(custom_workflow)
response = await agent.chat("Write a creative analysis of this data")
```

### Multi-Stage Plugin Usage
```python
# Same plugin used in multiple stages
validation_workflow = {
    "parse": ["data_validator"],     # Validate input structure
    "review": ["data_validator"]     # Validate output quality
}

agent = Agent.from_workflow_dict(validation_workflow)
```

## Key Benefits

1. **Clear Mental Model**: Agent = Resources + Workflow is intuitive and powerful
2. **Zero friction start**: Agents work immediately with sensible defaults
3. **Intelligent defaults**: Production-capable local stack (Ollama + DuckDB + Files)
4. **Selective upgrade**: Override only what you need to change
5. **Flexible plugin reuse**: Same plugin can work across multiple appropriate stages
6. **Gradual complexity**: Start with templates, customize as needed
7. **Safe composition**: Validation prevents invalid plugin-stage combinations
8. **Personality through composition**: Agent behavior emerges from plugin choices
9. **Dual interface**: Anthropomorphic simplicity + technical power when needed
10. **Constructor injection**: Immediate validation with no incomplete state
11. **Development to production**: Same patterns scale from laptop to cloud

## Developer Guidelines

### Creating New Plugins
```python
class MyPlugin(PromptPlugin):
    supported_stages = [THINK, REVIEW]  # Declare supported stages
    dependencies = ["llm", "memory"]     # Required resources

    def validate_config(self) -> ValidationResult:
        # Implement creation-time validation
        if self.assigned_stage not in self.supported_stages:
            return ValidationResult.error(f"Unsupported stage: {self.assigned_stage}")

    async def validate_runtime(self) -> ValidationResult:
        # Implement runtime connectivity validation
        pass

    async def _execute_impl(self, context: PluginContext) -> None:
        # Runtime safety check
        if context.current_stage not in self.supported_stages:
            raise UnsupportedStageError(f"Unsupported stage: {context.current_stage}")

        # Use temporary thoughts for inter-stage communication
        await context.think("my_analysis", analysis_result)

        # Use persistent memory for user data
        await context.remember("user_preference", user_data)
```

### Creating Workflow Templates
```yaml
workflows:
  my_agent_type:
    parse: [my_parser_plugin]
    think: [my_reasoning_plugin]
    review: [my_reasoning_plugin]  # Same plugin, different stage
    output: [my_formatter_plugin]
    # Missing stages inherit from defaults
```

This architecture provides a foundation for building powerful, flexible AI agents while maintaining simplicity and developer productivity through clear mental models, progressive disclosure, and intelligent defaults.
