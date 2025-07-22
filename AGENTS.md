# Entity Pipeline Contributor Guide

This repository contains a plugin-based framework for building AI agents.
Use this document when preparing changes or reviewing pull requests.

## Critical Guidance
- **CRITICAL:** Before beginning any work, please read the this file completely. You _must_ comply with the architecture defined below.
- If something is not explicitly stated in this document, it is **not** allowed.  Create a `AGENT NOTE:` instead.
- The project is unreleased.  Do not support legacy, deprecated, or backwards compatibility.
- Prefer adding `TODO:` comments when scope is unclear.
- Create `AGENT NOTE:` comments for other agents.
- Always use the Poetry environment for development.
- Run `poetry install --with dev` before executing any quality checks or tests.
- Run tests using `poetry run poe test` or related tasks to ensure `PYTHONPATH` is set.
- Run integration tests with Docker using `poetry run poe test-with-docker`.







# Entity Framework: Complete Architecture Guide

## Overview

The Entity framework provides a **unified agent architecture** combining a **4-layer resource system** with a **6-stage workflow**. This enables immediate development through zero-config defaults while supporting seamless progression to production-grade configurations.

## Core Mental Model

### Agent Composition
```python
Agent = Resources + Workflow + Infrastructure
```

An **Agent** consists of three primary components:
- **Resources**: Shared capabilities (LLM, Memory, Storage) that plugins can access
- **Workflow**: Stage-specific plugin assignments that define the agent's processing behavior and personality  
- **Infrastructure**: Deployment and scaling patterns from local Docker to cloud production

### Agent Personality Through Plugin Composition
Agent personality and capabilities emerge from the specific plugins assigned to each workflow stage:

- **Helpful Assistant**: Friendly reasoning plugins + polite formatters
- **Data Analyst**: Statistical analysis plugins + chart generators
- **Creative Writer**: Imagination plugins + storytelling formatters

## Core Architecture: 4-Layer Resource System

### Layer Hierarchy with Constructor Injection

The framework uses strict dependency layers to prevent circular dependencies and ensure predictable initialization:

```python
# Layer 1: Infrastructure Primitives (concrete technology)
duckdb_infra = DuckDBInfrastructure("./agent_memory.duckdb")
ollama_infra = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
s3_infra = S3Infrastructure(bucket="my-bucket")

# Layer 2: Resource Interfaces (technology-agnostic APIs)
db_resource = DatabaseResource(duckdb_infra)
vector_resource = VectorStoreResource(duckdb_infra) 
llm_resource = LLMResource(ollama_infra)
storage_resource = StorageResource(s3_infra)

# Layer 3: Canonical Agent Resources (guaranteed building blocks)
memory = Memory(db_resource, vector_resource)  # Constructor injection
llm = LLM(llm_resource)
storage = Storage(storage_resource)

# Layer 4: Agent with Workflow (resources + processing workflow)
agent = Agent(resources=[memory, llm, storage], workflow=my_workflow)
```

### Resource Dependency Rules

```python
class Memory(AgentResource):
    """Layer 3: Canonical building blocks - depend only on Layer 2"""
    
    def __init__(self, database: DatabaseResource, vector_store: VectorStoreResource, config: Dict | None = None):
        # Constructor injection provides immediate validation
        self.database = database
        self.vector_store = vector_store
        self.config = config or {}
        
        # Validation at construction - no incomplete state
        if not database or not vector_store:
            raise ResourceInitializationError("Database and vector store required")

class SmartMemory(AgentResource):
    """Layer 4: Custom compositions - depend only on Layer 3"""
    
    def __init__(self, memory: Memory, llm: LLM, config: Dict | None = None):
        self.memory = memory
        self.llm = llm
        
    async def contextual_recall(self, query: str) -> Dict[str, Any]:
        """Smart recall with LLM-enhanced semantic search"""
        results = await self.memory.vector_search(query, k=5)
        context = await self.llm.generate(f"Summarize relevant context: {results}")
        return {"results": results, "summary": context.content}
```

### Core Canonical Resources (Layer 3)

The framework guarantees these three resources are available to every workflow:

```python
class StandardResources:
    llm: LLM           # Unified LLM interface for reasoning
    memory: Memory     # External persistence for conversations and data  
    storage: Storage   # File and object storage capabilities
```

## 6-Stage Workflow

### Workflow
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

Each stage serves a specific purpose with clear termination control:

- **INPUT**: Receive and initially process user requests
- **PARSE**: Extract and structure important information  
- **THINK**: Perform reasoning, planning, and decision-making
- **DO**: Execute actions, tool calls, and external operations
- **REVIEW**: Validate results and ensure response quality
- **OUTPUT**: Format and deliver final responses (ONLY stage that can terminate workflow)

### Response Termination Control

**Decision**: Only OUTPUT stage plugins can set the final response that terminates the workflow iteration loop.

```python
# THINK stage - store analysis in persistent memory
class ReasoningPlugin(PromptPlugin):
    stage = THINK
    
    async def _execute_impl(self, context: PluginContext) -> None:
        analysis = await self.call_llm(context, "Analyze this request...")
        await context.remember("reasoning_result", analysis.content)
        # No context.say() - plugin cannot terminate workflow

# OUTPUT stage - compose final response and terminate
class ResponsePlugin(PromptPlugin):
    stage = OUTPUT
    
    async def _execute_impl(self, context: PluginContext) -> None:
        reasoning = await context.recall("reasoning_result", "")
        response = await self.call_llm(context, f"Respond based on: {reasoning}")
        
        await context.say(response.content)  # This terminates the workflow
```

**Workflow continues looping through all stages until an OUTPUT plugin calls `context.say()`**

## Layer 0: Zero-Config Development Strategy

### Automatic Resource Defaults

Layer 0 provides immediate functionality with zero configuration using local-first resources:

```python
# This just works - no config files needed
from entity import Agent

agent = Agent()  # Automatically uses Layer 0 defaults

# Automatically configured:
# - Ollama LLM (localhost:11434, llama3.2:3b)  
# - DuckDB Memory (./agent_memory.duckdb)
# - LocalFileSystem Storage (./agent_files/)
# - Default workflow with basic plugins per stage

response = await agent.chat("What's 5 * 7?")
```

### Plugin Registration via Configuration

```python
# Simple workflow configuration
simple_workflow = {
    "input": ["web_input_plugin"],
    "parse": ["entity_extractor_plugin"],
    "think": ["reasoning_plugin"],
    "do": ["calculator_plugin"],
    "review": ["quality_checker_plugin"],
    "output": ["formatter_plugin"]
}

agent = Agent.from_workflow_dict(simple_workflow)
response = await agent.chat("What's 15 * 23?")
```

### Fallback Behavior Rules

```python
# 1. No Configuration → Layer 0 Defaults
agent = Agent()  # Uses Ollama + DuckDB + LocalFileSystem

# 2. Partial Configuration → Selective Override  
agent = Agent.from_config({
    "plugins": {
        "resources": {
            "llm": {"type": "openai", "model": "gpt-4"}
            # memory, storage use Layer 0 defaults
        }
    }
})

# 3. Full Configuration → No Defaults
agent = Agent.from_config("config.yaml")  # Everything explicit
```

## Plugin System Architecture

### Universal Plugin Base Class

All framework extensions inherit from a single base with explicit stage declaration:

```python
class Plugin(ABC):
    """Universal extension point - all framework extensions inherit from this"""
    supported_stages = [THINK]  # Default stage support
    dependencies = []           # Required resources
    
    def validate_config(self) -> ValidationResult:
        """Configuration syntax, required fields, dependency declarations"""
        if hasattr(self, 'assigned_stage') and self.assigned_stage not in self.supported_stages:
            return ValidationResult.error(f"Plugin not supported in {self.assigned_stage}")
    
    def validate_workflow(self, workflow: Workflow) -> ValidationResult:
        """Validate plugin usage within workflow context"""
        if self.assigned_stage not in workflow.supported_stages:
            return ValidationResult.error(f"Workflow doesn't support stage {self.assigned_stage}")
        return ValidationResult.success()
        
    async def execute(self, context: PluginContext) -> Any:
        # Runtime safety check
        if context.current_stage not in self.supported_stages:
            raise UnsupportedStageError(f"Plugin cannot run in {context.current_stage}")
        return await self._execute_impl(context)
    
    @abstractmethod
    async def _execute_impl(self, context: PluginContext) -> Any:
        """Plugin-specific implementation"""
```

### Plugin Categories with Stage Restrictions

```python
# Processing plugins with stage flexibility
class PromptPlugin(Plugin):
    """LLM-based reasoning and processing logic"""
    supported_stages = [THINK, REVIEW]  # Can reason or validate
    dependencies = ["llm"]
    
class ToolPlugin(Plugin):
    """External function calls and actions"""
    supported_stages = [DO]  # Actions only in DO stage
    dependencies = []

# Interface plugins with specific purposes  
class InputAdapterPlugin(Plugin):
    """Convert external input into workflow messages"""
    supported_stages = [INPUT]
    
class OutputAdapterPlugin(Plugin):
    """Convert workflow responses to external formats"""
    supported_stages = [OUTPUT]
```

### Multi-Stage Plugin Support

```python
class ValidationPlugin(PromptPlugin):
    supported_stages = [PARSE, REVIEW]  # Author-defined limitations
    
    async def _execute_impl(self, context: PluginContext) -> None:
        if context.current_stage == PARSE:
            await self._validate_input_structure(context)
        elif context.current_stage == REVIEW:
            await self._validate_output_quality(context)

# Workflow can use same plugin in multiple stages
workflows:
  careful_analyst:
    parse: [validation_plugin]     # ✅ Supported
    review: [validation_plugin]    # ✅ Supported  
    think: [validation_plugin]     # ❌ Error - not in supported_stages
```

### Plugin Execution Order

**Decision**: Plugins execute in YAML configuration order within each stage.

```yaml
plugins:
  prompts:
    reasoning_step_1: {...}    # Runs first in THINK stage
    reasoning_step_2: {...}    # Runs second in THINK stage  
    final_decision: {...}      # Runs third in THINK stage
```

## State Management & Context: Persistent Memory Pattern

### Unified Memory Interface for All State

The framework uses persistent Memory for all state management - no temporary storage:

```python
class BasicPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # All state persisted to Memory - nothing temporary
        await context.remember("analysis_result", result)      # Store persistent data
        analysis = await context.recall("analysis_result")     # Retrieve persistent data
        
        # User-specific data automatically namespaced by user_id
        await context.remember("user_prefs", data)             # User-specific storage
        prefs = await context.recall("user_prefs")             # User-specific retrieval
        
        # Conversation operations
        await context.say("Here's my response")                # Final response (OUTPUT only)
        history = await context.conversation()                 # Get conversation history
        last_msg = await context.listen()                      # Get last user message
```

### Direct Resource Access for Advanced Operations

```python
class AdvancedPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Advanced interface - complex operations
        memory = context.get_resource("memory")
        results = await memory.query("SELECT * FROM user_prefs WHERE category = ?", ["style"])
        similar = await memory.vector_search("user preferences", k=5)
        
        # Tool execution patterns
        result = await context.tool_use("weather", location="SF")  # Immediate execution
        context.queue_tool_use("search", query="AI news")         # Queued execution
        
        # Still can use simple memory interface
        await context.remember("search_results", similar)
```

### Inter-Stage Communication via Persistent Memory

Plugins communicate across stages using persistent memory that survives across workflow iterations:

```python
# INPUT stage - capture initial request
class InputPlugin(InputAdapterPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        await context.remember("user_intent", "weather query")

# PARSE stage - structure information
class ParsePlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        user_intent = await context.recall("user_intent", "")
        await context.remember("location", "San Francisco")

# THINK stage - analyze and plan
class ThinkPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        location = await context.recall("location", "")
        await context.remember("analysis", f"User wants weather for {location}")

# OUTPUT stage - compose final response using all persistent data
class OutputPlugin(OutputAdapterPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        analysis = await context.recall("analysis", "")
        await context.say(f"Based on analysis: {analysis}")
```

## Tool System Architecture

### Tool Execution Patterns

**Decision**: Support both immediate and queued tool execution patterns:

```python
class ActionPlugin(ToolPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Immediate execution - synchronous workflow
        weather = await context.tool_use("weather", location="SF")
        await context.remember("weather_data", weather)
        
        # Queued execution - parallel processing
        context.queue_tool_use("search", query="SF weather")
        context.queue_tool_use("news", topic="weather alerts")
        # Tools execute automatically between workflow stages
```

### Tool Discovery Architecture

**Decision**: Lightweight registry query with plugin-level orchestration logic:

```python
class SmartToolSelectorPlugin(PromptPlugin):
    async def _execute_impl(self, context: PluginContext) -> None:
        # Discover available tools
        available_tools = context.discover_tools(category="weather")
        
        # Plugin implements selection logic
        best_tool = self._rank_tools_by_relevance(available_tools, context.message)
        result = await context.tool_use(best_tool.name, location="San Francisco")
        await context.remember("selected_tool", best_tool.name)
```

## Error Handling & Validation

### 2-Phase Validation Workflow

**Decision**: Fail-fast error handling with comprehensive startup validation:

```python
class PluginValidation:
    # Phase 1: Quick validation (<100ms)
    def validate_config(self) -> ValidationResult:
        """Configuration syntax, plugin structure, dependency conflicts"""
        
    # Phase 2: Workflow compatibility validation (<1s)  
    def validate_workflow(self, workflow: Workflow) -> ValidationResult:
        """Stage compatibility, workflow requirements, plugin ordering"""
```

### Failure Propagation Strategy

**Decision**: Fail-fast error propagation where any plugin failure immediately fails the stage and triggers ERROR stage processing.

```python
# Failed plugin immediately terminates stage execution
# ERROR stage plugins provide user-friendly error responses
class BasicErrorPlugin(FailurePlugin):
    stage = ERROR
    
    async def _execute_impl(self, context: PluginContext) -> None:
        error_info = context.failure_info
        await context.say(f"I encountered an error: {error_info.user_message}")
```

## Multi-User Support & Scaling

### Stateless Workers with Persistent State

**Decision**: Framework implements stateless worker processes with externally-persistent conversation state:

```python
class WorkflowWorker:
    def __init__(self, registries: SystemRegistries):
        self.registries = registries  # Shared resource pools only - no user data
    
    async def execute_workflow(self, workflow_id: str, message: str, *, user_id: str) -> Any:
        # Load conversation state from external storage each request
        memory = self.registries.resources.get("memory")
        conversation = await memory.load_conversation(f"{user_id}_{workflow_id}")
        
        # Execute with ephemeral state (discarded after response)
        state = WorkflowState(conversation=conversation, workflow_id=workflow_id)
        result = await self.run_stages(state)
        
        # Persist updated state back to external storage
        await memory.save_conversation(f"{user_id}_{workflow_id}", state.conversation)
        return result
```

### Multi-User Support via user_id Parameter

**Decision**: Simple `user_id` parameter provides user isolation through conversation namespacing:

```python
# Same agent instance handles multiple users
agent = Agent.from_config("support-bot.yaml")

# User isolation through external persistence namespacing
response1 = await agent.chat("Hello, I need help", user_id="user123")
response2 = await agent.chat("Hi there", user_id="user456")  # Completely isolated

class PluginContext:
    async def remember(self, key: str, value: Any) -> None:
        """User-specific persistent storage with automatic namespacing"""
        namespaced_key = f"{self.user_id}:{key}"
        await self._memory.store_persistent(namespaced_key, value)
```

## Infrastructure & Deployment

### Docker + OpenTofu Architecture

**Decision**: Composable infrastructure using Docker for local development and OpenTofu with Terragrunt for cloud deployment:

```python
# Same agent config everywhere
agent = Agent.from_config("agent.yaml")

# Local development
docker_infra = DockerInfrastructure()
await docker_infra.deploy(agent)

# Production deployment (same agent)
aws_infra = AWSStandardInfrastructure()
await aws_infra.deploy(agent)
```

### CLI as Input/Output Adapter

The `ent` command-line tool is implemented as an Adapter supporting both Input and Output stages:

```python
class EntCLIAdapter(InputAdapterPlugin, OutputAdapterPlugin):
    """CLI tool that handles both input collection and output formatting"""
    supported_stages = [INPUT, OUTPUT]
    
    async def _execute_impl(self, context: PluginContext) -> None:
        if context.current_stage == INPUT:
            await self._handle_cli_input(context)
        elif context.current_stage == OUTPUT:
            await self._format_cli_output(context)
            
    async def _handle_cli_input(self, context: PluginContext) -> None:
        # Parse command line arguments and user input
        user_message = self._get_user_input()
        await context.remember("cli_input", user_message)
        
    async def _format_cli_output(self, context: PluginContext) -> None:
        # Format and display response to terminal
        response = await context.recall("final_response", "")
        self._display_to_terminal(response)
```

### Infrastructure Management Commands

```bash
# Local development
ent infra init docker --profile development
ent infra deploy --local

# Cloud deployment
ent infra init aws-standard --region us-east-1
ent infra deploy --cloud

# Test locally → Deploy to cloud
ent infra test --local
ent infra migrate --from docker --to aws-standard

# Agent management
ent agent create my-agent --template helpful-assistant
ent agent deploy my-agent --environment production
ent agent logs my-agent --follow
```

## Configuration & Environment Management

### Environment Variable Substitution

**Decision**: All plugins implement recursive `${VAR}` substitution with `.env` auto-discovery:

```python
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
    # Handle dict, list recursively...
```

```yaml
# config.yaml with environment substitution
plugins:
  resources:
    llm:
      api_key: ${OPENAI_API_KEY}
      model: ${LLM_MODEL}
    database:
      host: ${DB_HOST}
      password: ${DB_PASS}
```

### Configuration Validation with Pydantic

**Decision**: Use Pydantic models exclusively for all configuration validation:

```python
class HTTPAdapterConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(ge=1, le=65535, default=8000)
    dashboard: bool = False

class HTTPAdapter(AdapterPlugin):
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        try:
            HTTPAdapterConfig(**config)
            return ValidationResult.success()
        except ValidationError as e:
            return ValidationResult.error(str(e))
```

### Configuration Hot-Reload Scope

**Decision**: Support only parameter changes for hot-reload; topology changes require restart:

- **Supported**: Parameter updates (temperature, timeouts, API keys, model settings)
- **Requires Restart**: Plugin additions/removals, stage reassignments, dependency changes

## Plugin Discovery & Distribution

### Git-Based Distribution

**Decision**: Git repositories as primary distribution mechanism with CLI installation tools:

```bash
# Git-based installation
ent plugin install https://github.com/user/weather-plugin
ent plugin install git@company.com:internal/custom-tools

# Plugin management
ent plugin list
ent plugin update weather-plugin
ent plugin uninstall weather-plugin
```

```yaml
# Plugin manifest (entity-plugin.yaml in repo root)
name: weather-plugin
version: 1.0.0
permissions: [external_api, storage]
dependencies: [requests, aiohttp]
entry_point: weather_plugin.WeatherPlugin
supported_stages: [DO, REVIEW]
```

## Observability & Monitoring

### Unified Logging System

**Decision**: `LoggingResource` provides unified, multi-output logging for all agent components:

```python
# All components use the same logging interface
logger = context.get_resource("logging")

await logger.log("info", "Plugin execution started",
                 component="plugin",
                 user_id=context.user_id,
                 workflow_id=context.workflow_id,
                 stage=context.current_stage,
                 plugin_name=self.__class__.__name__)
```

### Shared Metrics Collection

**Decision**: `MetricsCollectorResource` automatically injected into all plugins for unified performance tracking:

```python
class BasePlugin:
    dependencies = ["metrics_collector"]  # Automatic for all plugins
    
    async def execute(self, context: PluginContext) -> Any:
        # Automatic metric collection wrapper
        start_time = time.perf_counter()
        try:
            result = await self._execute_impl(context)
            await self.metrics_collector.record_plugin_execution(
                plugin_name=self.__class__.__name__,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                success=True
            )
            return result
        except Exception as e:
            # Error metrics automatically collected
            raise
```

## Development Guidelines

### Creating New Plugins

```python
class MyPlugin(PromptPlugin):
    supported_stages = [THINK, REVIEW]  # Declare supported stages
    dependencies = ["llm", "memory"]     # Required resources
    
    def validate_config(self) -> ValidationResult:
        """Implement creation-time validation"""
        if self.assigned_stage not in self.supported_stages:
            return ValidationResult.error(f"Unsupported stage: {self.assigned_stage}")
        
    def validate_workflow(self, workflow: Workflow) -> ValidationResult:
        """Validate plugin usage within workflow"""
        if not workflow.supports_stage(self.assigned_stage):
            return ValidationResult.error(f"Workflow doesn't support {self.assigned_stage}")
        return ValidationResult.success()
        
    async def _execute_impl(self, context: PluginContext) -> None:
        # Use persistent memory for all state
        await context.remember("my_analysis", analysis_result)
        
        # User-specific data automatically namespaced
        await context.remember("user_preference", user_data)
        
        # Final response (OUTPUT stage only)
        if context.current_stage == OUTPUT:
            await context.say("My response")
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

### Progressive Complexity Examples

```python
# Layer 0: Zero config
agent = Agent()

# Layer 1: Named workflows
agent = Agent.from_workflow("helpful_assistant")

# Layer 2: Custom workflows
agent = Agent.from_workflow_dict({
    "think": ["analytical_reasoning", "creativity_booster"],
    "output": ["markdown_formatter"]
})

# Layer 3: Full configuration
agent = Agent.from_config("production-config.yaml")
```

## Key Architectural Benefits

1. **Clear Mental Model**: Agent = Resources + Workflow + Infrastructure
2. **Zero friction start**: Agents work immediately with sensible defaults
3. **Stateless scaling**: Horizontal scaling through external persistence
4. **Multi-user support**: Simple user isolation through namespacing
5. **Progressive complexity**: Start simple, add sophistication as needed
6. **Fail-fast validation**: Errors caught at startup, not runtime
7. **Persistent state only**: All state stored in Memory - no temporary data
8. **Constructor injection**: Immediate validation with no incomplete state
9. **Universal plugin system**: Single interface for all extensions
10. **CLI as Adapter**: Command-line tool implemented as Input/Output adapter
11. **Production-ready**: Built-in observability, security, and deployment patterns

This architecture provides a foundation for building powerful, scalable AI agents while maintaining developer productivity through clear mental models, progressive disclosure, and intelligent defaults that scale from local development to production deployment.