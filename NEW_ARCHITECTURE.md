# Entity Framework Architecture Guide

## Overview

The Entity framework provides a **4-layer resource architecture** with **Layer 0 zero-config defaults** that enable immediate development while supporting seamless progression to production-grade configurations.

## Core Architecture: 4-Layer Resource System

### Layer Composition with Constructor Injection

```python
# Layer 1: Infrastructure Primitives (concrete technology)
duckdb_infra = DuckDBInfrastructure("./agent_memory.duckdb")
ollama_infra = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
s3_infra = S3Infrastructure(bucket="my-bucket")

# Layer 2: Concrete Resource Implementations (technology-specific logic)
db_resource = DuckDBDatabaseResource(duckdb_infra)
vector_resource = DuckDBVectorStoreResource(duckdb_infra)
llm_resource = OllamaLLMResource(ollama_infra)
storage_resource = S3StorageResource(s3_infra)

# Layer 3: Canonical Agent Resources (unified interfaces)
memory = Memory(db_resource, vector_resource)  # Constructor injection
llm = LLM(llm_resource)
storage = Storage(storage_resource)

# Layer 4: Agent (individual canonical resources for ergonomics)
agent = Agent(memory=memory, storage=storage, llm=llm)
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
    
    def __init__(self, llm: LLM, memory: Memory, config: Dict | None = None):
        self.llm = llm        # Constructor injection
        self.memory = memory  # Constructor injection
```

## Layer 0: Zero-Config Development Strategy

### Automatic Resource Defaults

Layer 0 acts as intelligent fallbacks that automatically provide working resources when no explicit configuration exists:

```python
# This just works - no config files needed
from entity import agent

@agent.prompt
def chat(message: str) -> str:
    return f"Respond to: {message}"

@agent.tool
def calculator(expression: str) -> float:
    return eval(expression)

# Automatically uses Layer 0 defaults:
# - Ollama LLM (localhost:11434, llama3.2:3b)
# - DuckDB Memory (./agent_memory.duckdb) 
# - LocalFileSystem Storage (./agent_files/)
response = agent.chat("What's 5 * 7?")
```

### Fallback Behavior Rules

1. **No Configuration → Layer 0 Defaults**
```python
agent = Agent()  # Uses Ollama + DuckDB + LocalFileSystem
```

2. **Partial Configuration → Selective Override**
```python
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {"type": "openai", "model": "gpt-4"}
            # memory, storage use Layer 0 defaults
        }
    }
})
```

3. **Full Configuration → No Defaults**
```python
# If config.yaml specifies all three resources, no defaults used
agent = Agent.from_config("config.yaml")
```

## Configuration Options

### Zero Config (Layer 0 Defaults)
```python
@agent.prompt
def helper(message: str) -> str:
    return f"Help with: {message}"

agent.chat("Hello")  # Works immediately
```

### Partial Configuration (Layer 0 + Custom)
```python
# Override just LLM, keep other defaults
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {
                "type": "entity.resources.llm:OpenAILLMResource",
                "api_key": "sk-...",
                "model": "gpt-4"
            }
            # memory and storage automatically use Layer 0 defaults
        }
    }
})

@agent.prompt 
def analyze(text: str) -> str:
    return f"Analyze: {text}"

# Uses: OpenAI LLM + DuckDB Memory + LocalFileSystem Storage
```

### Full Configuration (Explicit Control)
```yaml
# config.yaml - explicit resource configuration
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

  prompts:
    analyzer:
      type: my_company.plugins:AnalyzerPlugin
```

```python
# No Layer 0 defaults used - everything explicit
agent = Agent.from_config("config.yaml")
response = agent.chat("Analyze this...")  # Uses PostgreSQL + S3 + GPT-4
```

### Implicit Agent Pattern

Decorators register to default agent instance for maximum simplicity:

```python
# Functions register to implicit 'agent' instance
@agent.prompt
def analyze(text: str) -> str:
    return f"Analyze: {text}"

@agent.tool
def calculator(expression: str) -> float:
    return eval(expression)

# Works immediately with Layer 0 defaults
response = agent.chat("What's 5 * 7?")  # Uses Ollama + DuckDB + LocalFileSystem
```

## Plugin Context: Dual Interface Pattern

### Anthropomorphic Interface for Simplicity

```python
class BasicPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Simple interface - most common usage
        await context.remember("user_prefs", data)     # Persistent storage
        prefs = await context.recall("user_prefs")     # Persistent retrieval
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
```

## Simplified State Model

**No Temporary State** - data either persists or goes in responses:

```python
# ❌ Removed: temporary thoughts
# await context.think("analysis", result)
# analysis = await context.reflect("analysis")

# ✅ Use: persistent memory or direct response
await context.remember("user_analysis", result)  # Persists across conversations
await context.say(f"Analysis: {result}")         # Include in response
```

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
```

## Key Benefits

1. **Zero friction start**: `@agent.prompt` functions work immediately
2. **Intelligent defaults**: Production-capable local stack (Ollama + DuckDB + Files)
3. **Selective upgrade**: Override only what you need to change
4. **Clear migration path**: Natural progression from simple to sophisticated
5. **No surprise behavior**: Explicit config always wins over defaults
6. **Development to production**: Same patterns scale from laptop to cloud
7. **Dual interface**: Anthropomorphic simplicity + technical power when needed
8. **Constructor injection**: Immediate validation with no incomplete state
9. **Simplified state**: Data persists or goes in responses, no temporary storage











## Plugin Validation Requirements

**Decision**: Every plugin implements mandatory `validate_config()` (synchronous) and `validate_runtime()` (asynchronous) methods called during agent startup. All validations must pass or the entire system fails with detailed error attribution.

**Implementation Pattern**:
```python
class BasePlugin:
    def validate_config(self) -> ValidationResult:
        """Synchronous validation: config syntax, required fields, dependency declarations"""
        
    async def validate_runtime(self) -> ValidationResult:
        """Asynchronous validation: external connectivity, infrastructure readiness"""

# Startup Validation Sequence:
# 1. Load configuration and inject dependencies
# 2. Call validate_config() on all plugins (fail-fast on any error)
# 3. Call validate_runtime() on all plugins in parallel (fail-fast on any error)
# 4. Only proceed to agent execution if all validations pass
```

**Validation Scope**:
- **Config validation**: Syntax correctness, required fields, dependency availability, parameter ranges
- **Runtime validation**: Database connectivity, API key validity, external service accessibility, file system permissions, hardware requirements

**Benefits**: Eliminates runtime surprises, provides clear startup error attribution, ensures consistent system state, and improves debugging through early failure detection.













## Plugin Discovery Architecture

**Decision**: Git-based plugin distribution with CLI installation tools. Future registry integration planned as ecosystem grows.

**Implementation Pattern**:
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
```

**Core Features**:
- **Git repositories**: Primary distribution mechanism for public and private plugins
- **Plugin manifests**: Declare permissions, dependencies, and entry points
- **CLI management**: Install, uninstall, list, and update commands  
- **Validation pipeline**: Automatic structure and security validation during install
- **Permission model**: User confirms plugin capabilities before installation
- **Local cache**: Downloaded plugins stored in `~/.entity/plugins/`

**Security Model**:
- Plugin manifests declare required permissions (API access, file system, network)
- Install-time validation of plugin structure and dependencies
- User explicit confirmation for permission grants
- Sandboxed execution environment for untrusted plugins

**Future Growth**: Optional centralized registry (`registry.entity.dev`) will enable shortened commands (`entity-cli plugin install weather`) while maintaining full Git URL support for private and custom plugins.











## Plugin Discovery Architecture

**Decision**: Git-based plugin distribution with CLI installation tools. Future registry integration planned as ecosystem grows.

**Implementation Pattern**:
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
```

**Core Features**:
- **Git repositories**: Primary distribution mechanism for public and private plugins
- **Plugin manifests**: Declare permissions, dependencies, and entry points
- **CLI management**: Install, uninstall, list, and update commands  
- **Validation pipeline**: Automatic structure and security validation during install
- **Permission model**: User confirms plugin capabilities before installation
- **Local cache**: Downloaded plugins stored in `~/.entity/plugins/`

**Security Model**:
- Plugin manifests declare required permissions (API access, file system, network)
- Install-time validation of plugin structure and dependencies
- User explicit confirmation for permission grants
- Sandboxed execution environment for untrusted plugins

**Future Growth**: Optional centralized registry (`registry.entity.dev`) will enable shortened commands (`entity-cli plugin install weather`) while maintaining full Git URL support for private and custom plugins.
