# Entity Pipeline Framework - Complete Architecture

## Executive Summary

The Entity Pipeline Framework is a **hybrid pipeline-state machine architecture** for building AI agents that combines the predictability of linear processing with the adaptability of intelligent looping. The framework enables developers to build sophisticated AI agents through a **three-layer plugin system** with **runtime reconfiguration** capabilities.

**Key Innovation**: Automatic pipeline iteration when no response is generated, creating state machine behavior within a pipeline mental model.

## Core Architecture Principles

### 1. Hybrid Pipeline-State Machine Design

The framework operates as a **linear pipeline with intelligent looping**:

```
PARSE → THINK → DO → REVIEW → DELIVER
  ↑                                ↓
  └── Loop if context.response is None
```

**Pipeline Stages:**
- **PARSE**: Input validation, context setup, memory retrieval (first pass)
- **THINK**: Intent classification, reasoning, planning, memory retrieval (second pass)
- **DO**: Tool execution, action taking
- **REVIEW**: Response generation, safety checks, formatting
- **DELIVER**: Output transmission, logging
- **ERROR**: Failure handling with user-friendly messages

**State Machine Behavior:**
- If `context.response` is `None` at pipeline end, automatically loops back to PARSE
- Maximum iterations prevented by `max_iterations` limit (defaults to 5)
- Exceeding limit triggers ERROR stage with failure response
- Each iteration builds upon previous context and conversation history

### 2. Three-Layer Plugin System

**Layer 1: Function-Based (Adoption)**
```python
@agent.plugin
async def weather_check(context):
    """Auto-classified as ToolPlugin, auto-routed to DO stage"""
    return await get_weather(context.location)
```

**Layer 2: Class-Based (Primary Usage)**  
```python
class WeatherToolPlugin(ToolPlugin):
    stages = [PipelineStage.DO]
    
    async def execute_function(self, params):
        return await self.get_weather(params['location'])
```

**Layer 3: Advanced (Sophisticated Control)**
```python
class ChainOfThoughtPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["database", "llm"]
    
    async def _execute_impl(self, context):
        # Full pipeline access with iteration control
        for step in range(self.config.get("max_steps", 5)):
            reasoning = await self.call_llm(context, prompt)
            if "final answer" in reasoning.content.lower():
                break
        context.set_response(final_answer)
```

### 3. Canonical Resource Architecture

Every pipeline has access to three core resource types:

#### LLM Resource
```python
# Unified provider interface
llm = context.get_resource("llm")
response = await llm.generate("What is 2+2?")

# Supports: OpenAI, Ollama, Claude, Gemini, Bedrock, Echo
```

#### Memory Resource  
```python
# Cognition-like interface with conversation management
memory = context.get_resource("memory")

# Conversation persistence
await memory.save_conversation(context.pipeline_id, history)
history = await memory.load_conversation(context.pipeline_id)

# Semantic search
similar = await memory.search_similar("user question", k=5)

# Contextual memory (short-term within pipeline)
memory.remember("user_preference", "concise")
preference = memory.recall("user_preference")

# ConversationManager is part of Memory resource
conversation_manager = memory.get_conversation_manager()
```

#### Storage Resource
```python
# File operations
storage = context.get_resource("storage")
path = await storage.store_file("data.json", content)
content = await storage.load_file("data.json")
```

### 4. Resource Composition Pattern

Resources are composed from simpler backends:

```python
# Simple setup
memory = MemoryResource(
    database=SQLiteDatabaseResource("./agent.db")
)

# Production setup  
memory = MemoryResource(
    database=PostgresResource(connection_str),
    vector_store=PgVectorStore(postgres, dimensions=768)
)

storage = StorageResource(
    filesystem=S3FileSystem(bucket="agent-files")
)
```

MemoryResource is a composite store that defaults to a DuckDB-backed database in
memory and supports optional SQL/NoSQL and vector backends. Because this default
uses an in-memory DuckDB database, there is no separate `InMemoryResource`.

## Plugin System Details

### Plugin Base Classes

```python
class ResourcePlugin(BasePlugin):
    """Infrastructure: LLM, Memory, Storage"""
    async def initialize(self) -> None
    async def health_check(self) -> bool
    
class ToolPlugin(BasePlugin):  
    """Functions: Calculator, Search, Weather"""
    async def execute_function(self, params) -> Any
    
class PromptPlugin(BasePlugin):
    """Processing: Reasoning, Memory, Formatting"""
    stages = [PipelineStage.THINK]  # Usually
    
class AdapterPlugin(BasePlugin):
    """I/O: HTTP, WebSocket, CLI"""
    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]
    
class FailurePlugin(BasePlugin):
    """Error Handling: User-friendly error messages"""
    stages = [PipelineStage.ERROR]
```

### Stage Assignment Rules

- **PARSE**: Input adapters, memory loading, validation
- **THINK**: Reasoning, planning, intent classification  
- **DO**: Tool execution, action taking
- **REVIEW**: Response formatting, safety checks
- **DELIVER**: Output adapters, logging
- **ERROR**: Failure handling (minimal plugins recommended)

### Tool Execution Model

**Immediate Execution (Best Practice)**:
```python
async def _execute_impl(self, context):
    # Tools execute immediately with natural async/await
    result = await context.use_tool("calculator", expression="2+2")
    context.set_response(f"The answer is {result}")
```

**Benefits**:
- Intuitive developer experience
- Clear error handling  
- Immediate feedback
- Natural async/await patterns
- No queuing complexity

**Note**: `context.execute_tool()` is deprecated in favor of `context.use_tool()` for consistency.

## State Management

### Pipeline State (Per-Execution)
```python
@dataclass
class PipelineState:
    conversation: List[ConversationEntry]
    response: Any = None  # If None at end, triggers loop
    stage_results: Dict[str, Any]
    metadata: Dict[str, Any]
    pipeline_id: str
    current_stage: PipelineStage
    max_iterations: int = 5  # Prevents infinite loops
    current_iteration: int = 0
    failure_info: Optional[FailureInfo] = None
```

### Context Interface (Plugin Access)
```python
class PluginContext:
    # Resource access
    def get_resource(self, name: str) -> Resource
    def get_llm(self) -> LLM
    
    # Tool execution (immediate)
    async def use_tool(self, tool_name: str, **params) -> Any
    
    # Response control
    def set_response(self, response: Any) -> None
    def has_response(self) -> bool
    
    # Conversation
    def add_conversation_entry(self, content: str, role: str)
    def get_conversation_history(self) -> List[ConversationEntry]
    
    # Memory shortcuts (cognitive interface)
    def remember(self, key: str, value: Any) -> None  
    def recall(self, key: str, default=None) -> Any
    def think(self, thought: str) -> None
```

### Memory Persistence Strategy

- **PipelineState**: Cleared after each pipeline execution (ephemeral)
- **ConversationHistory**: Persisted via Memory resource across interactions
- **Resource State**: Managed by individual resource lifecycles
- **ConversationManager**: Integrated into Memory resource, not separate component

## Runtime Reconfiguration

### Supported Changes
- **LLM Provider Swapping**: OpenAI ↔ Ollama without restart (framework is LLM agnostic)
- **Plugin Configuration**: Update parameters, retry settings at runtime
- **Resource Backends**: SQLite → PostgreSQL migration while running
- **Tool Addition**: Add new capabilities dynamically
- **Memory Backends**: Switch from in-memory to persistent storage

### Configuration Update Process
```python
# 1. Validation
result = plugin.validate_config(new_config)

# 2. Dependency Check  
deps_ok = plugin.validate_dependencies(registry)

# 3. Graceful Update (wait for pipeline completion)
await wait_for_pipeline_completion()
await plugin.reconfigure(new_config)

# 4. Cascade to Dependents
for dependent in registry.get_dependents(plugin_name):
    await dependent.on_dependency_reconfigured(plugin_name, old, new)
```

### Restart Required Cases
- Pipeline stage assignment changes (happens at instantiation/reconfiguration)
- Core framework updates
- Plugins that explicitly don't support runtime reconfiguration

## Error Handling & Reliability

### Failure Flow
```
Plugin Error → FailureInfo → ERROR Stage → User-Friendly Response
```

### Circuit Breaker Pattern
```python
class BasePlugin:
    failure_threshold: int = 3
    failure_reset_timeout: float = 60.0
    
    # Automatic circuit breaking on repeated failures
```

### Static Fallback
```python
# When ERROR stage plugins fail
STATIC_ERROR_RESPONSE = {
    "error": "System error occurred", 
    "message": "An unexpected error prevented processing your request.",
    "pipeline_id": pipeline_id,
    "type": "static_fallback"
}
```

## Developer Experience Features

### Progressive Complexity
1. **Start Simple**: Function decorators with auto-classification
2. **Add Structure**: Class-based plugins with explicit control  
3. **Full Power**: Advanced plugins with sophisticated capabilities

### Cognitive Interface
```python
# Natural, cognition-like methods for intuitive development
if context.is_question():
    response = await context.ask_llm("Answer this question: " + context.message)
    
if context.contains("weather", "temperature"):
    weather = await context.use_tool("weather", location=context.location)

# Memory operations with semantic meaning
memory = context.get_resource("memory")
relevant_context = await memory.get_memory(context.message)  # Similarity search
```

### Observability Built-In
- **Automatic Logging**: Request ID tracking, structured JSON logs
- **Metrics Collection**: Plugin duration, LLM usage, tool execution
- **Tracing Support**: OpenTelemetry integration
- **Health Monitoring**: Resource health checks, circuit breaker status

## Configuration Example

```yaml
plugins:
  resources:
    llm:
      type: pipeline.resources.llm.unified:UnifiedLLMResource
      provider: ollama
      model: llama3:8b
      base_url: http://localhost:11434
      
    memory:
      type: pipeline.resources.memory_resource:MemoryResource  
      database:
        type: plugins.builtin.resources.postgres:PostgresResource
        host: localhost
        name: agent_db
      vector_store:
        type: plugins.builtin.resources.pg_vector_store:PgVectorStore
        dimensions: 768
        
    storage:
      type: pipeline.resources.storage_resource:StorageResource
      filesystem:
        type: plugins.builtin.resources.s3_filesystem:S3FileSystem
        bucket: agent-files
        
  tools:
    calculator:
      type: plugins.builtin.tools.calculator_tool:CalculatorTool
      
  prompts:
    reasoning:
      type: plugins.builtin.prompts.complex_prompt:ComplexPrompt
      max_steps: 5
```

## Deployment Patterns

### Development
```python
# Simple setup
agent = Agent("config/dev.yaml")
await agent.serve_http(port=8000)
```

### Production  
```python
# With resource pools and monitoring
agent = Agent("config/prod.yaml")
server = AgentServer(agent.runtime)
await server.serve_http(host="0.0.0.0", port=8000)
```

### Container Deployment
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["python", "-m", "entity", "--config", "config/prod.yaml", "serve-http"]
```

## Architecture Benefits

### For Developers
- **Mental Model Clarity**: Pipeline stages are intuitive
- **Progressive Disclosure**: Simple → Complex as needed
- **Hot Reconfiguration**: Change behavior without restarts
- **Rich Tooling**: Built-in observability and debugging

### For Operations  
- **Reliable Execution**: Circuit breakers, automatic retry
- **Observable by Design**: Comprehensive logging and metrics
- **Scalable Architecture**: Stateless workers, external state
- **Container Ready**: Docker/Kubernetes deployment patterns

### For AI Systems
- **Hybrid Intelligence**: Predictable + Adaptive behavior  
- **Multi-Turn Capable**: Automatic conversation management
- **Tool Integration**: Immediate access to external capabilities
- **Memory Persistence**: Context across conversations

## Future Extensibility

The architecture supports evolution through:

- **Plugin Ecosystem**: Community-contributed capabilities
- **Provider Diversity**: Multiple LLM/storage backends  
- **Deployment Flexibility**: Local, cloud, edge environments
- **Integration Patterns**: REST, GraphQL, gRPC, WebSocket
- **Advanced Patterns**: Multi-agent, workflow orchestration

---

*This architecture enables developers to build AI agents that are both simple to start with and capable of sophisticated behaviors, while maintaining production reliability and operational visibility.*