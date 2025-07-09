# Architecture Decisions Summary

The following architecture decisions were made through systematic analysis of the Entity Pipeline Framework to optimize for developer adoption, scalability, and maintainability.

* [0. Folder Structure and Naming Conventions](#0-folder-structure-and-naming-conventions)
* [1. Core Mental Model: Plugin Taxonomy and Architecture](#1-core-mental-model-plugin-taxonomy-and-architecture)
* [2. Progressive Disclosure: Enhanced 3-Layer Plugin System](#2-progressive-disclosure-enhanced-3-layer-plugin-system)
* [3. Resource Management: Core Canonical + Simple Flexible Keys](#3-resource-management-core-canonical--simple-flexible-keys)
* [4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults](#4-plugin-stage-assignment-guided-explicit-declaration-with-smart-defaults)
* [5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation](#5-error-handling-and-validation-fail-fast-with-multi-layered-validation)
* [6. Scalability Architecture: Stateless Workers with External State](#6-scalability-architecture-stateless-workers-with-external-state)
* [6. Response Termination Control](#6-response-termination-control)
* [7. Stage Results Accumulation Pattern](#7-stage-results-accumulation-pattern)
* [8. Tool Execution Patterns](#8-tool-execution-patterns)
* [9. Memory Resource Consolidation](#9-memory-resource-consolidation)
* [10. Resource Dependency Injection Pattern](#10-resource-dependency-injection-pattern)
* [11. Plugin Stage Assignment Precedence](#11-plugin-stage-assignment-precedence)
* [12. Resource Lifecycle Management](#12-resource-lifecycle-management)
* [13. Configuration Hot-Reload Scope](#13-configuration-hot-reload-scope)
* [14. Error Handling and Failure Propagation](#14-error-handling-and-failure-propagation)
* [15. Pipeline State Management Strategy](#15-pipeline-state-management-strategy)
* [16. Plugin Execution Order Simplification](#16-plugin-execution-order-simplification)
* [17. Agent and AgentBuilder Separation](#17-agent-and-agentbuilder-separation)
* [18. Configuration Validation Consolidation](#18-configuration-validation-consolidation)
* [19. Reasoning Pattern Abstraction Strategy](#19-reasoning-pattern-abstraction-strategy)
* [20. Memory Architecture: Primitive Resources + Custom Plugins](#20-memory-architecture-primitive-resources--custom-plugins)
* [21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration](#21-tool-discovery-architecture-lightweight-registry-query--plugin-level-orchestration)
* [22. Plugin System Architecture: Explicit Configuration with Smart Defaults](#22-plugin-system-architecture-explicit-configuration-with-smart-defaults)
* [23. State Management Consolidation: Unified Cache/Memory Pattern](#23-state-management-consolidation-unified-cachememory-pattern)
* [24. Agent Instantiation Unification: Single Agent Class Pattern](#24-agent-instantiation-unification-single-agent-class-pattern)
* [25. Workflow Objects with Progressive Complexity](#25-workflow-objects-with-progressive-complexity)
* [26. Workflow Objects: Composable Agent Blueprints](#26-workflow-objects-composable-agent-blueprints)

## 0. Folder Structure and Naming Conventions

## Repository Layout

Folder structure:
```plaintext
entity/
├── user_plugins/              # Example or custom plugins for local use or sharing
│
├── src/
│   └── entity/                # Main Python package
│       ├── core/              # Core execution engine and orchestration logic
│       ├── plugins/           # Plugin definitions grouped by type
│       ├── resources/         # Composed resource interfaces (memory, storage, llm)
│       ├── config/             # Configuration models and validation logic
│       ├── cli/               # Developer CLI tools and utilities
│       └── utils/             # Misc shared utilities (logging, retries, etc.)
│
└── tests/                     # Unit and integration tests
    ├── test_core/             # Tests for pipeline, agent, and context
    ├── test_plugins/          # Tests for plugin behaviors and base classes
    ├── test_resources/        # Tests for memory, storage, and LLM resources
    ├── test_config/            # Tests for config model parsing and validation
    └── test_cli/              # Tests for CLI commands and developer tools
```


## 1. Core Mental Model: Plugin Taxonomy and Architecture

The Entity Pipeline Framework uses a unified plugin architecture where all extensions inherit from a single `Plugin` base class. This design follows the universal extension pattern found in frameworks like Blender's Node system, providing a consistent interface while supporting diverse functionality.

```python
class Plugin(ABC):
    """Universal extension point - all framework extensions inherit from this"""
    
    # Universal lifecycle
    async def validate_config(self, config) -> ValidationResult: ...
    async def validate_dependencies(self, registry) -> ValidationResult: ...
    async def initialize(self) -> None: ...  # Optional
    async def shutdown(self) -> None: ...    # Optional
    
    # Stage execution (execution plugins only)
    async def execute(self, context) -> Any: ...  # Required for stage-based plugins
```

### **Plugin Categories**

#### **Infrastructure Plugins (ResourcePlugin)**
Persistent services that provide capabilities to other plugins. These initialize once during startup and remain available throughout the pipeline lifecycle.

**Characteristics:**
- Initialize during startup phase, before any pipeline execution
- Provide shared services (databases, APIs, storage)
- Never execute during pipeline stages
- Have complex dependency relationships and composition patterns

**Subtypes:**
```python
class LLMResourcePlugin(ResourcePlugin):
    """Provides language model capability"""
    resource_type: str = "llm"
    # Examples: OpenAIProvider, OllamaProvider, ClaudeProvider

class DatabaseResourcePlugin(ResourcePlugin):  
    """Provides persistent storage capability"""
    resource_type: str = "database"
    # Examples: PostgresResource, SQLiteResource, DuckDBResource

class VectorStoreResourcePlugin(ResourcePlugin):
    """Provides semantic search capability"""  
    resource_type: str = "vector_store"
    # Examples: PgVectorStore, MemoryVectorStore

class FileSystemResourcePlugin(ResourcePlugin):
    """Provides file storage capability"""
    resource_type: str = "filesystem" 
    # Examples: LocalFileSystem, S3FileSystem, MemoryFileSystem
```

#### **Processing Plugins (Execution Plugins)**
Functional units that execute during specific pipeline stages to transform data, make decisions, or perform actions.

**PromptPlugin - Reasoning and Planning**
```python
class PromptPlugin(Plugin):
    """LLM-based reasoning and processing logic"""
    stages = [PipelineStage.THINK]  # Default stage assignment
    
    # Examples: ConversationHistory, ComplexPrompt, MemoryRetrieval
```

**ToolPlugin - External Function Calls**
```python
class ToolPlugin(Plugin):
    """External API calls and function execution"""
    stages = [PipelineStage.DO]  # Default stage assignment
    
    async def execute_function(self, params: Dict[str, Any]) -> Any: ...
    
    # Examples: CalculatorTool, WeatherAPI, SearchTool
```

#### **Interface Plugins (AdapterPlugin)**
Handle input/output transformation and protocol adaptation between external systems and the pipeline.

**InputAdapterPlugin - Media Ingestion**
```python
class InputAdapterPlugin(AdapterPlugin):
    """Convert external input into pipeline messages"""
    stages = [PipelineStage.PARSE]  # Default stage assignment
    
    # Examples: HTTPAdapter, CLIAdapter, STTAdapter, WebSocketAdapter
```

**OutputAdapterPlugin - Response Delivery**
```python
class OutputAdapterPlugin(AdapterPlugin):
    """Convert pipeline responses to external formats"""
    stages = [PipelineStage.DELIVER]  # Default stage assignment
    
    # Examples: JSONFormatter, TTSAdapter, LoggingAdapter
```

#### **Specialized Plugins**

**FailurePlugin - Error Handling**
```python
class FailurePlugin(Plugin):
    """Error recovery and user-friendly error responses"""
    stages = [PipelineStage.ERROR]
    
    # Examples: BasicLogger, ErrorFormatter, FallbackErrorPlugin
```

**InfrastructurePlugin - Operational Concerns**
```python
class InfrastructurePlugin(Plugin):
    """Deployment, monitoring, and operational support"""
    # Examples: MetricsCollector, DockerDeployment, TerraformProvisioning
```

### **Resource Composition Architecture**

The framework guarantees three concrete resources are available to every pipeline execution:

#### **Required Resources**
```python
class StandardResources:
    llm: LLM           # Composed from LLMResourcePlugin instances
    memory: Memory     # Composed from DatabaseResourcePlugin + VectorStoreResourcePlugin  
    storage: Storage   # Composed from FileSystemResourcePlugin instances
```

#### **Composition Rules**
Resources are assembled from compatible ResourcePlugins based on `resource_type` declarations:

```python
# LLM Resource Composition
llm = UnifiedLLMResource([
    OpenAIProvider(config),      # LLMResourcePlugin
    OllamaProvider(config),      # LLMResourcePlugin (fallback)
])

# Memory Resource Composition  
memory = Memory(
    database=PostgresResource(config),        # DatabaseResourcePlugin
    vector_store=PgVectorStore(config),       # VectorStoreResourcePlugin
)

# Storage Resource Composition
storage = Storage(
    filesystem=S3FileSystem(config)           # FileSystemResourcePlugin
)
```

### **Plugin Lifecycle Management**

#### **Two-Phase Lifecycle**
```python
# Phase 1: Infrastructure Initialization (ResourcePlugins)
for resource_plugin in dependency_order:
    await resource_plugin.initialize()
    container.register(resource_plugin)

# Phase 2: Pipeline Execution (Processing Plugins)
for stage in [PARSE, THINK, DO, REVIEW, DELIVER]:
    plugins = registry.get_plugins_for_stage(stage) 
    for plugin in plugins:
        await plugin.execute(context)
```

#### **Lifecycle Characteristics**
- **ResourcePlugins**: Initialize once → persist → shutdown at end
- **Processing Plugins**: Execute per-request → stateless between executions
- **AdapterPlugins**: May run continuously (HTTP server) or per-request (CLI)

### **Plugin Development Patterns**

#### **Stage Assignment Precedence**
1. **Explicit declaration**: `stages = [PipelineStage.THINK]` always wins
2. **Type defaults**: ToolPlugin → DO, PromptPlugin → THINK, etc.
3. **Auto-classification**: Analyze function source for stage hints

#### **Dependency Declaration**
```python
class ComplexPlugin(PromptPlugin):
    dependencies = ["database", "vector_store"]  # Explicit dependency list
    
    def __init__(self, config):
        super().__init__(config)
        # Dependencies injected by container after construction
        self.database = None      # Set by container
        self.vector_store = None  # Set by container
```

#### **Plugin Registration Order**
Plugins execute in YAML configuration order within each stage:
```yaml
plugins:
  prompts:
    step_1: {...}    # Runs first in THINK stage
    step_2: {...}    # Runs second in THINK stage  
    step_3: {...}    # Runs third in THINK stage
```

### **Benefits of Unified Plugin Architecture**

1. **Single Learning Curve** - Developers master one Plugin interface for all extensions
2. **Consistent Tooling** - Same CLI commands, documentation patterns, and development tools work across all plugin types
3. **Unified Ecosystem** - Plugin marketplace, examples, and community resources share common patterns
4. **Flexible Composition** - Mix and match plugins to create custom agent behaviors
5. **Clear Extension Points** - Obvious places to add functionality without framework modifications

### **Plugin Validation and Discovery**

The framework automatically validates plugin configurations to ensure:
- Required resource types are present (LLM, Memory, Storage)
- ResourcePlugin composition rules are followed
- Stage assignments are compatible with plugin types
- Dependency chains are valid and acyclic
- Configuration parameters match plugin requirements

This taxonomy provides a clear mental model for developers while maintaining the flexibility to extend the framework in any direction through the universal Plugin interface.

## 2. Progressive Disclosure: Enhanced 3-Layer Plugin System

**Decision**: Maintain current 3-layer structure with improved transitions and guided discovery.

**Layer Structure**:
- **Layer 1**: Function decorators (`@agent.plugin`) with auto-classification
- **Layer 2**: Class-based plugins with explicit control  
- **Layer 3**: Advanced plugins with sophisticated pipeline access

**Enhancements**:
- Automated upgrade suggestions when functions become complex
- Template generators via CLI: `poetry run python src/cli.py upgrade-plugin my_function`
- Interactive stage assignment guidance
- Progressive Context API reveal: hide advanced methods behind `context.advanced.*`

**Rationale**: Research shows 3-4 abstraction levels hit the cognitive sweet spot while avoiding analysis paralysis.

## 3. Resource Management: Core Canonical + Simple Flexible Keys

**Decision**: Hybrid approach maintaining simple defaults while enabling complex scenarios.

**Structure**:
- **Core canonical names**: `llm`, `memory`, `storage` for simple mental model
- **Flexible arbitrary keys**: `chat_gpt`, `claude_reasoning`, `postgres_prod`, etc.
- **Flat configuration**: Each resource key gets complete independent config
- **No inheritance complexity**: No forced hierarchical naming conventions

**Benefits**:
- 80% of use cases remain simple with canonical names
- Enables multi-provider scenarios: `context.get_resource("chat_gpt")` 
- Supports environment variations and plugin isolation
- Maintains resource composition patterns without complexity

**Usage Examples**:
```python
# Simple canonical usage
llm = context.get_resource("llm")

# Complex multi-provider usage  
reasoning_llm = context.get_resource("chat_gpt")
embedding_llm = context.get_resource("local_embeddings")
prod_db = context.get_resource("postgres_prod")
```

## 4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults

**Decision**: Use explicit stage declaration with intelligent guidance and automation to reduce cognitive load.

**Core Strategy**: Balance predictability with simplicity through smart defaults and interactive guidance.

**Implementation Pattern**:

**1. Smart Default Assignment Based on Plugin Type**:
```python
# ToolPlugin auto-defaults to DO stage
class WeatherPlugin(ToolPlugin):
    # stages = [PipelineStage.DO]  # Implicit default
    
# PromptPlugin auto-defaults to THINK stage  
class ReasoningPlugin(PromptPlugin):
    # stages = [PipelineStage.THINK]  # Implicit default
    
# AdapterPlugin auto-defaults to PARSE + DELIVER
class HTTPAdapter(AdapterPlugin):
    # stages = [PipelineStage.PARSE, PipelineStage.DELIVER]  # Implicit default

# Explicit override when needed
class ComplexPlugin(ToolPlugin):
    stages = [PipelineStage.THINK, PipelineStage.DO]  # Override default
```

**2. Interactive Stage Discovery**:
- CLI command: `poetry run python src/cli/plugin_tool.py analyze-plugin my_plugin.py`
- The tool inspects async functions and suggests stages based on `PluginAutoClassifier` heuristics.
- Provides stage recommendations with clear reasoning

**3. Clear Stage Mental Model**:
- **PARSE**: "What do I need to understand the input?"
- **THINK**: "What should I decide or plan?"
- **DO**: "What actions should I take?"
- **REVIEW**: "Is my response good enough?"
- **DELIVER**: "How should I send the output?"

**Progressive Complexity Path**:
1. **Level 1**: Function decorators with auto-assignment based on behavior analysis
2. **Level 2**: Explicit stage declaration with validation and smart defaults
3. **Level 3**: Multi-stage plugins with conditional execution logic

**Validation and Safety**:
- **Dependency validation**: Ensure PARSE plugins don't depend on DO stage results
- **Circular dependency detection**: Prevent infinite loops in multi-stage plugins
- **Stage conflict resolution**: Handle plugins that want the same stage with different priorities

**Benefits**:
- **Familiar patterns**: Explicit declaration aligns with successful frameworks (Airflow, Prefect)
- **Reduced cognitive load**: Smart defaults handle 80% of cases correctly
- **Debugging clarity**: Developers know exactly when and why plugins run
- **Scalability**: Clear stage boundaries prevent architectural complexity
- **Compliance ready**: Explicit flows support audit trails and regulatory requirements

**Rationale**: Research shows that explicit declaration with intelligent assistance provides the best balance of control, predictability, and developer experience. Avoids complexity overhead of automatic routing while reducing learning curve of pure manual assignment.

## 5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation

**Decision**: Implement fail-fast error handling with comprehensive startup validation through staged validation pipelines.

**Core Philosophy**: Surface errors quickly with detailed technical information while preventing cascading failures through aggressive circuit breakers.

**Three-Phase Validation Pipeline**:
- **Phase 1**: Quick validation (<100ms) - configuration syntax, plugin structure, dependency conflicts
- **Phase 2**: Dependency validation (<1s) - circular dependency detection, missing resources, version compatibility
- **Phase 3**: Runtime validation (background) - external connectivity, database connections, API accessibility

**Implementation Pattern**:
```python
class BasePlugin:
    @classmethod
    async def validate_config(cls, config) -> ValidationResult:
        """Phase 1: Quick syntax/structure validation"""
        
    @classmethod 
    async def validate_dependencies(cls, registries) -> ValidationResult:
        """Phase 2: Dependency graph validation"""
        
    async def validate_runtime(self) -> ValidationResult:
        """Phase 3: External connectivity validation (background)"""
```

**Circuit Breaker Integration**:
- Database connections: 3 failures = circuit open
- External APIs: 5 failures = circuit open  
- File systems: 2 failures = circuit open
- All failures surface with full technical details for debugging

**Developer Experience Features**:
- CLI validation tools: `poetry run python src/cli.py validate --config config.yaml`
- Dependency graph visualization: `poetry run python src/cli.py graph-dependencies`
- Actionable error messages with specific remediation steps
- Progressive validation during development with hot-reload

**Benefits**:
- **Predictable failures**: Issues caught at startup, not during runtime
- **Fast feedback**: Critical validation completes in under 1 second
- **Clear debugging**: Technical errors with full context and remediation steps
- **Production reliability**: Comprehensive validation prevents system instability
- **Developer productivity**: Clear error messages and validation tooling

**Rationale**: Research shows staged validation pipelines with fail-fast philosophy provide optimal balance of startup performance, system reliability, and developer experience. Aggressive circuit breakers prevent cascading failures while maintaining transparency about system health.


```markdown
## 6. Scalability Architecture: Stateless Workers with External State

**Decision**: Framework implements stateless worker pattern where pipeline execution maintains no local state between requests.

**Implementation Pattern**:
```python
# Pipeline workers are stateless - no instance variables for conversation data
class PipelineWorker:
    def __init__(self, registries: SystemRegistries):
        self.registries = registries  # Shared resource pools only
    
    async def execute_pipeline(self, pipeline_id: str, message: str) -> Any:
        # Load all context from external storage each request
        memory = self.registries.resources.get("memory")
        conversation = await memory.load_conversation(pipeline_id)
        
        # Execute pipeline with ephemeral state
        state = PipelineState(conversation=conversation, pipeline_id=pipeline_id)
        result = await self.run_stages(state)
        
        # Save updated context to external storage
        await memory.save_conversation(pipeline_id, state.conversation)
        return result
```

**Resource Implementation**:
```python
# Resources manage connection pooling, not conversation state
class MemoryResource:
    def __init__(self, database: DatabaseResource):
        self.db_pool = database.get_connection_pool()  # Shared pool
    
    async def load_conversation(self, pipeline_id: str) -> List[ConversationEntry]:
        # Load from external store each time
        async with self.db_pool.acquire() as conn:
            return await conn.fetch_conversation(pipeline_id)
    
    async def save_conversation(self, pipeline_id: str, conversation: List[ConversationEntry]):
        # Persist to external store
        async with self.db_pool.acquire() as conn:
            await conn.store_conversation(pipeline_id, conversation)
```

**Key Requirements**:
- Workers hold no conversation state between requests
- All context loaded fresh from `MemoryResource` per pipeline execution
- `PipelineState` cleared after each execution
- Resources provide connection pooling, not data persistence
- Any worker instance can process any conversation through external state loading

**Benefits**: Linear horizontal scaling, worker processes are disposable, conversation continuity through external persistence, standard container orchestration patterns applicable.



## 6. Response Termination Control

**Decision**: Only DELIVER stage plugins can set the final pipeline response that terminates the iteration loop.

**Rationale**: 
- Creates clear separation of concerns across pipeline stages
- PARSE validates and loads context
- THINK performs reasoning and planning  
- DO executes tools and actions
- REVIEW validates and formats intermediate results
- DELIVER handles final response composition and output transmission
- Prevents early termination from skipping important downstream processing
- Makes pipeline flow predictable and debuggable

**Implementation**: 
- `context.set_response()` method restricted to DELIVER stage plugins only
- Pipeline continues looping (PARSE → THINK → DO → REVIEW → DELIVER) until a DELIVER plugin calls `set_response()`
- Earlier stages use `context.store()` to store intermediate outputs for DELIVER plugins to access
- Maximum iteration limit (default 5) prevents infinite loops when no DELIVER plugin sets a response

**Benefits**: Ensures consistent output processing, logging, and formatting while maintaining the hybrid pipeline-state machine mental model.

## 7. Stage Results Accumulation Pattern

**Decision**: Use stage results accumulation with `context.store()`, `context.load()`, and `context.has()` methods for inter-stage communication.

**Rationale**:
- Builds on existing stage results infrastructure with intuitive naming
- Maintains pipeline mental model where each stage produces discrete outputs
- Stage results persist across pipeline iterations, enabling context accumulation
- Provides explicit traceability for debugging and observability
- Allows flexible composition patterns in DELIVER plugins

**Implementation**:
- Earlier stages use `context.store(key, value)` to save intermediate outputs
- DELIVER plugins use `context.load(key)` to access stored results for response composition
- `context.has(key)` enables conditional logic based on available results
- Stage results are cleared between separate pipeline executions but persist across iterations within the same execution

**Benefits**: Clear data flow, debugging visibility, flexible response composition, and natural support for iterative pipeline execution.

## 8. Tool Execution Patterns

**Decision**: Support both immediate and queued tool execution with `context.tool_use()` and `context.queue_tool_use()` methods.

**Rationale**:
- Different mental models serve different use cases effectively
- Immediate execution provides simple synchronous workflow for single tool calls
- Queued execution enables parallel processing and batch optimization
- Supports existing concurrency controls in ToolRegistry
- Enables coordination patterns where multiple tool results need collective processing

**Implementation**:
- `context.tool_use(name, **params)` executes tools immediately and returns results
- `context.queue_tool_use(name, **params)` queues tools for parallel execution at stage boundaries
- Queued tools execute automatically between pipeline stages
- Both patterns support the same tool interface and retry mechanisms

**Usage Guidance**: Use `tool_use()` by default for simplicity. Use `queue_tool_use()` when you need multiple independent tool calls that can run in parallel or when processing results collectively.
 
## 9. Memory Resource Consolidation

**Decision**: Consolidate all memory-related components into a single unified `Memory` resource with embedded `ConversationHistory`.

**Rationale**:
- Eliminates architectural ambiguity between separate memory components
- Single responsibility for all memory concerns (key-value, conversations, search)
- Simplifies resource dependencies - plugins only need "memory" resource
- Cleaner configuration with one memory section instead of multiple
- Natural API progression from simple to advanced usage patterns

**Implementation**:
- `Memory` class provides `get()`, `set()`, `clear()` for key-value storage
- `memory.conversation_history` property exposes advanced conversation management
- Convenience methods `save_conversation()` and `load_conversation()` delegate to embedded ConversationHistory
- Optional database and vector_store backends for persistence and similarity search
- Replaces SimpleMemoryResource, MemoryResource, ConversationManager, and Memory interface

**Usage**: `memory = context.get_resource("memory")` provides access to all memory functionality through a single resource interface.


## 10. Resource Dependency Injection Pattern

**Decision**: Use explicit dependency declaration with container injection for all resource-to-resource relationships.

**Rationale**:
- Enables complete dependency graph validation at startup
- Supports hot-reload by tracking dependency chains for restart coordination
- Makes system architecture visible through configuration
- Improves testability through dependency injection
- Prevents circular dependency issues through topological sorting
- Aligns with existing SystemInitializer dependency resolution patterns

**Implementation**:
- Resources declare dependencies in `dependencies = ["database", "vector_store"]` class attribute
- Container instantiates resources in dependency order
- Dependencies injected as attributes after construction: `memory.database = container.get("database")`
- Dependencies can be optional (None) for degraded operation modes
- DependencyGraph validates entire system before initialization

**Benefits**: Startup validation, clear architecture visibility, hot-reload support, and robust dependency management across the entire resource system.

## 11. Plugin Stage Assignment Precedence

**Decision**: Use layered approach with strict precedence hierarchy for plugin stage assignment.

**Precedence Order (highest to lowest)**:
1. **Explicit `stages` attribute** - declared in plugin class always wins
2. **Plugin type defaults** - ToolPlugin → DO, PromptPlugin → THINK, AdapterPlugin → PARSE+DELIVER
3. **Auto-classification** - analyze function source code for stage hints (function-based plugins only)

**Rationale**:
- Supports progressive disclosure from simple defaults to explicit control
- Predictable override behavior - developers know explicit declarations always win
- Enables flexible patterns like planning tools in THINK stage or validation tools in REVIEW
- Clear debugging path - easy to trace why plugins are assigned to specific stages
- Maintains backward compatibility with existing auto-classification

**Implementation**:
- Allow explicit stage overrides even when they conflict with type conventions
- Log warnings when explicit stages deviate from type defaults for visibility
- Auto-classification only applies to function-based plugins without explicit stages
- Document common override patterns and use cases

**Benefits**: Flexibility for advanced use cases while maintaining simple defaults and predictable behavior for debugging and system understanding.

## 12. Resource Lifecycle Management

**Decision**: Use strict sequential initialization with fail-fast behavior for all resources.

**Rationale**:
- Predictable failure points with clear error attribution
- No partial state confusion or cascading dependency failures
- Simple mental model - resources initialize in dependency order or system fails
- Deterministic behavior ensures same configuration produces same results
- Easier debugging with single failure mode instead of complex degraded states

**Implementation**:
- Initialize resources one at a time in topological dependency order
- Fail immediately if any resource initialization or health check fails
- Shutdown resources in reverse dependency order during cleanup
- Clear error messages identifying exactly which resource failed and why
- No degraded mode operation - system is either fully functional or stopped

**Benefits**: Eliminates partial initialization debugging complexity, provides clear failure attribution, and ensures consistent system state across deployments.

## 13. Configuration Hot-Reload Scope

**Decision**: Support only parameter changes for hot-reload; all other configuration changes require full restart.

**Supported Hot-Reload**:
- Parameter changes - Update existing plugin configs (temperature, timeouts, API keys, model settings)

**Requires Restart**:
- Plugin additions/removals
- Stage reassignments  
- Dependency changes
- New resource types

**Rationale**:
- Parameter changes cover 80% of hot-reload use cases with minimal complexity
- Topology changes create hard-to-reproduce state issues and debugging complexity
- Dependency validation gaps can emerge from runtime plugin/resource changes
- Partial effects on running pipelines create inconsistent system state
- Restricting scope ensures predictable, reliable hot-reload behavior

**Implementation**:
- Validate that configuration changes only modify parameters of existing plugins
- Reject hot-reload requests that attempt topology changes with clear restart requirement
- Provide fast restart mechanisms for development workflows requiring topology changes

**Benefits**: Reliable parameter tuning in production while maintaining system stability and predictable debugging paths.

## 14. Error Handling and Failure Propagation

**Decision**: Use fail-fast error propagation where any plugin failure immediately fails the stage and triggers ERROR stage processing.

**Rationale**:
- Clear debugging with exact failure attribution - no cascading confusion
- Predictable behavior ensures same failures produce same results
- Aligns with strict sequential resource initialization philosophy
- Simple mental model where pipeline succeeds completely or fails at specific point
- Prevents bad state propagation from partially failed stages to downstream processing

**Implementation**:
- Plugin failure immediately terminates stage execution
- Failed stage triggers ERROR stage with FailureInfo context
- ERROR stage plugins provide user-friendly error responses and recovery logic
- Circuit breakers and retries operate at individual plugin level before failure propagation
- Clear separation between normal processing (fail fast) and error handling (ERROR stage)

**Benefits**: Simplified debugging paths, predictable failure behavior, clear error attribution, and graceful user experience through dedicated ERROR stage handling.

## 15. Pipeline State Management Strategy

**Decision**: Use Memory resource for conversation persistence and structured logging for debugging, eliminating separate state checkpoint mechanisms.

**Unified Approach**:
- **Conversation persistence** - Memory resource stores conversation history between pipeline executions
- **Debug visibility** - Structured logs capture stage completion with full context (stage results, tool calls, iteration count)
- **No state checkpoints** - Remove state file snapshots and serialization complexity

**Rationale**:
- Single source of truth through Memory resource eliminates duplicate persistence
- Structured logs provide searchable debugging without file management overhead
- Aligns with "Observable by Design" principle using existing logging infrastructure
- Eliminates state file cleanup and serialization complexity
- Log aggregation systems handle retention, rotation, and distributed debugging

**Implementation**:
- Remove `state_file` and `snapshots_dir` parameters from pipeline execution
- Log stage completion with pipeline context using `StateLogger`
- Use Memory resource for cross-execution conversation continuity
- Clean up state serialization utilities if no longer needed

**Benefits**: Simplified architecture, single persistence mechanism, scalable debugging through log infrastructure, and elimination of file-based state management complexity.

## 16. Plugin Execution Order Simplification

**Decision**: Plugins execute in the order defined in the YAML configuration.

**Rationale**:
- YAML order provides clear, visible execution sequence without mystery
- Simpler mental model - "plugins run in the order I list them"
- Easier debugging with predictable execution order
- Eliminates configuration ambiguity
- "What you see is what you get" approach reduces cognitive overhead

**Implementation**:
- Register plugins in YAML configuration order or list order

**Configuration Example**:
```yaml
plugins:
  prompts:
    reasoning_step_1: {...}    # Runs first
    reasoning_step_2: {...}    # Runs second
    final_decision: {...}      # Runs third
```

**Benefits**: Predictable execution sequence, simplified plugin development, clearer debugging, and elimination of an entire configuration dimension while maintaining full control over execution order.

## 17. Agent and AgentBuilder Separation

**Decision**: Use clear separation between `AgentBuilder` for programmatic construction and `Agent` for config-driven initialization.

**Responsibilities**:
- **AgentBuilder** - Programmatic agent construction for dynamic/code-based agents
- **Agent** - Config-driven agent initialization for YAML/production deployments

**Implementation**:
```python
class AgentBuilder:
    """Programmatic construction with plugin registration methods"""
    def add_plugin(self, plugin) -> None: ...
    def plugin(self, func, **hints) -> Callable: ...  # Decorator
    def load_plugins_from_directory(self, dir) -> None: ...
    def build_runtime(self) -> AgentRuntime: ...

class Agent:
    """Config-driven initialization with runtime execution"""
    def __init__(self, config_path: str): ...
    async def handle(self, message: str) -> Dict[str, Any]: ...
    
    @classmethod
    def from_builder(cls, builder: AgentBuilder) -> "Agent": ...
```

**Usage Patterns**:
- **Production**: `Agent("config.yaml")` for stable, configuration-managed deployments
- **Development**: `AgentBuilder()` for dynamic plugin registration and testing
- **Hybrid**: `Agent.from_builder(builder)` to combine programmatic and config approaches

**Benefits**: Single responsibility per class, clear intent distinction, no method duplication, easier testing and documentation with distinct use cases.

## 18. Configuration Validation Consolidation

**Decision**: Use Pydantic models exclusively for all configuration validation, eliminating JSON Schema approaches.

**Rationale**:
- Clear, field-specific error messages improve debugging experience
- Automatic type coercion reduces common configuration errors  
- Single validation pathway eliminates confusion about where config fails
- IDE support through type hints enhances developer experience
- Runtime validation supports hot-reload configuration changes
- Consistent validation approach across all plugin types

**Implementation**:
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

**Status**: Configuration validation now relies solely on Pydantic models. The
`entity/config` directory now handles configuration models; JSON Schema logic was removed.

**Benefits**: Single learning curve, better error attribution, type safety with automatic coercion, and consistent validation experience across the entire framework.

## Summary So Far ✅

### 19. Reasoning Pattern Abstraction Strategy

**Decision**: Provide built-in reasoning pattern plugins while maintaining full extensibility for custom patterns.

**Implementation**:
- **Built-in patterns**: Framework ships with common reasoning patterns as ready-to-use PromptPlugins
  - `ChainOfThoughtPlugin` - Iterative step-by-step reasoning
  - `ReActPlugin` - Reasoning + action + reflection loops  
  - `PlanAndExecutePlugin` - Goal decomposition and execution tracking
- **Full extensibility**: Users can inherit from built-in patterns or create completely custom PromptPlugins
- **Multiple customization paths**: Inheritance-based overrides, composition-based engines, and configuration-driven customization

**Usage Examples**:
```python
# Use built-in pattern
class MyReActPlugin(ReActPlugin):
    def customize_reflection_step(self, thought, action_result):
        # Override specific methods

# Full custom implementation  
class NovelReasoningPattern(PromptPlugin):
    # Complete custom reasoning logic
```

**Benefits**: 
- **Fast development**: Built-in patterns provide immediate value
- **Best practices**: Common patterns implemented with framework optimizations
- **No lock-in**: Full flexibility to implement novel reasoning approaches
- **Progressive complexity**: Start with built-ins, customize as needed

**Rationale**: Aligns with progressive disclosure philosophy - simple defaults for common cases, unlimited flexibility for advanced use cases.

### 20. Memory Architecture: Primitive Resources + Custom Plugins

**Decision**: Provide foundational memory primitives through unified Memory resource; users implement domain-specific memory patterns as plugins.

**Implementation**:
- **Framework provides**: Memory resource with SQL database + vector store capabilities
- **Users implement**: Custom memory plugins using these primitives (LongTermMemoryPlugin, ContextualMemoryPlugin, etc.)
- **No prescriptive solutions**: Framework remains pattern-agnostic for memory strategies

**Example**:
```python
class PersonalPreferencesPlugin(PromptPlugin):
    async def _execute_impl(self, context):
        memory = context.get_resource("memory")
        # SQL for structured user data
        prefs = await memory.database.query("SELECT style FROM user_prefs WHERE user_id=?", [context.user])
        # Vector for semantic context
        similar = await memory.vector_store.query_similar(context.message, k=3)
        context.store("user_style", prefs[0]["style"])
        context.store("relevant_context", similar)
```

**Rationale**: Maintains framework focus on providing powerful primitives rather than opinionated solutions. Enables unlimited memory patterns while keeping core simple.

### 21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration

**Decision**: Provide simple tool discovery primitive through registry queries; users implement discovery logic and tool orchestration in plugins.

**Implementation**:
- **Framework provides**: `context.discover_tools()` method that queries registered tools with optional filters
- **User control**: Only explicitly registered tools are discoverable
- **Plugin-level logic**: Users implement tool selection, ranking, and orchestration logic in custom plugins
- **Safety by design**: Tool registration equals tool permission - unregistered tools cannot be discovered

**Example**:
```python
class SmartToolSelectorPlugin(PromptPlugin):
    async def _execute_impl(self, context):
        available_tools = context.discover_tools(intent="weather_query")
        best_tool = self._rank_tools_by_relevance(available_tools, context.message)
        result = await context.tool_use(best_tool.name, location=extracted_location)
```

**Benefits**: 
- **Simple primitive**: Discovery is just registry query with filters
- **User flexibility**: Custom discovery and orchestration logic in plugins  
- **Security model**: Only registered tools are accessible
- **No framework bloat**: Avoids opinionated tool chaining solutions

**Rationale**: Maintains framework focus on providing useful primitives while letting users implement domain-specific tool orchestration strategies.


## 22. Plugin System Architecture: Explicit Configuration with Smart Defaults

**Decision**: The framework uses explicit configuration as the primary pattern, enhanced with intelligent defaults for common use cases.

### Rationale

**Rejected Pure Convention-Over-Configuration** due to:
- Fragile auto-inference of plugin stages via source code scanning
- Hidden failures and unpredictable behavior in production
- Circular import risks and increased startup complexity
- Difficulty meeting enterprise compliance and auditing requirements

**Rejected Pure Explicit Configuration** due to:
- Excessive boilerplate for simple use cases
- Developer friction requiring full module paths for everything
- Large, unmaintainable configuration files

### Implementation Pattern

```yaml
plugins:
  resources:
    llm: openai              # Canonical name with smart defaults
    database: postgres       # Auto-resolves to built-in implementations
    
  prompts:
    custom_reasoning:        # Explicit configuration when needed
      type: my_company.prompts.CustomReasoningPrompt
      stages: [think, review]
      config:
        max_iterations: 5
```

### Key Principles

1. **Canonical Names**: Built-in components use simple identifiers (`llm`, `database`, `memory`)
2. **Explicit Paths**: Custom plugins require full module paths for clarity
3. **Stage Defaults**: Plugin stages determined by class hierarchy, not source code analysis
4. **No Magic**: All behavior is predictable and debuggable through configuration

This approach provides rapid development for common scenarios while maintaining full control and transparency for complex enterprise deployments.

## 23. State Management Consolidation: Unified Cache/Memory Pattern

**Decision**: Replace the multi-layered state management system (PipelineState + PluginContext + Memory + Stage Results) with a unified StateManager using intuitive verb-based APIs.

### Rationale

**Eliminated Complexity** from the previous system:
- Four overlapping storage mechanisms (`context.store()`, `context.set_metadata()`, `memory.set()`, conversation history)
- Unclear boundaries between temporary vs persistent data
- Data duplication with conversation history in multiple locations
- High cognitive overhead deciding which storage method to use

### Unified API Pattern

```python
# In PluginContext - simple, intuitive verbs:
context.cache("analysis", result)     # Temporary data (dies with pipeline run)
context.recall("analysis")            # Retrieve temporary data

context.remember("user_prefs", data)  # Persistent data (survives sessions)
context.memory("user_prefs")           # Retrieve persistent data

context.say("Here's my response")      # Add to conversation history
context.conversation()                 # Get conversation history
```

### Key Principles

1. **Two-Tier Model**: Only temporary (cache/recall) vs persistent (remember/memory) storage
2. **Intuitive Verbs**: Method names match natural language for cognitive ease
3. **Single Responsibility**: Each method has one clear purpose and scope
4. **Conversation Special Case**: Chat history as a specialized persistent type
5. **No Overlap**: Eliminated redundant storage mechanisms and data duplication

This consolidation reduces four overlapping concepts to two clear patterns, dramatically simplifying the developer mental model while maintaining all necessary functionality.


## 24. Agent Instantiation Unification: Single Agent Class Pattern

**Decision**: Replace the dual-path system (Agent + AgentBuilder + AgentRuntime) with a single unified `Agent` class that handles all creation and execution patterns.

### Rationale

**Eliminated Complexity** from the previous system:
- Confusing choice between `Agent` vs `AgentBuilder` for different use cases
- Inconsistent interfaces across classes for similar functionality
- Scattered instantiation logic across multiple classes
- Separate `AgentRuntime` concept requiring additional mental overhead

### Unified API Pattern

```python
# Multiple construction methods
agent = Agent.from_config("config.yaml")        # Config-driven
agent = Agent()                                  # Programmatic
agent = Agent.from_directory("./plugins")       # Discovery-based
agent = Agent.from_package("my_company.agents") # Package-based

# Consistent plugin registration
agent.add_plugin(my_plugin)

@agent.plugin
def my_function(context):
    return "response"

# Unified execution interface
response = await agent.handle(message)     # Direct execution
await agent.serve_http(port=8000)         # HTTP server
await agent.serve_websocket(port=8001)    # WebSocket server
await agent.serve_cli()                   # CLI interface
```

### Key Principles

1. **Single Entry Point**: One `Agent` class for all use cases
2. **Method-Based Construction**: Multiple `from_*` class methods for different creation patterns
3. **Consistent Execution**: All serving patterns use the same underlying interface
4. **Progressive Complexity**: Simple cases remain simple, complex cases remain possible
5. **Internal Implementation**: `AgentBuilder` and `AgentRuntime` become private implementation details

This unification provides a single, learnable interface while maintaining all current functionality and flexibility.

## 25. Workflow Objects with Progressive Complexity

We will introduce **Workflow objects** that get passed to Pipeline for execution, maintaining the existing stage system as the foundation. 

**Implementation approach:**
- **Start with simple stage→plugin mappings** (Option A) for v1 implementation
- **Evolve to support conditional logic** (Option C) in future versions
- **Preserve existing architecture** - no breaking changes to current stage-based system

**Key benefits:**
- Maintains alignment with stateless execution model
- Preserves YAML configuration compatibility  
- Enables workflow reusability and testing
- Provides clear upgrade path from simple to complex workflows

**Example pattern:**
```python
# Simple v1 workflow
CustomerWorkflow = {
    Stage.PARSE: ["extract_info", "validate_account"],
    Stage.THINK: ["classify_issue", "route_specialist"],
    Stage.DO: ["resolution_tools"],
    Stage.DELIVER: ["format_response"]
}

pipeline = Pipeline(workflow=CustomerWorkflow)
agent = Agent(pipeline=pipeline)
```

This gives us the composability and reusability benefits immediately while maintaining the simplicity and reliability of the current stage-based execution model.

**Decisions Made So Far**: 
- ✅ Hybrid stateless/stateful lifecycle model  
- ✅ Need dev-to-prod documentation clarity
- ✅ Add Workflow objects with progressive complexity (simple→rich)
- ✅ Maintain existing stage system as foundation

Ready for the next architectural concern?

## 26. Workflow Objects: Composable Agent Blueprints

A **Workflow** is a reusable blueprint that defines which plugins execute in which pipeline stages. It separates the "what should happen" (workflow definition) from the "how it executes" (pipeline execution), enabling better composition, testing, and reusability.

**Core Purpose:**
- **Composition**: Mix and match different agent behaviors without rebuilding pipelines
- **Reusability**: Share common workflows across teams, projects, and deployments  
- **Testability**: Test workflow logic independently from execution infrastructure
- **Configurability**: Parameterize workflows for different environments or use cases

**How it works:**
```python
# Define what happens
workflow = CustomerServiceWorkflow()

# Define how it executes  
pipeline = Pipeline(approach=workflow)

# Combine them
agent = Agent(pipeline=pipeline)
```

**Key Design Principles:**
1. **Workflows are stateless blueprints** - they define behavior, not execution state
2. **Pipelines handle execution** - they manage resources, state, and plugin orchestration
3. **Clean separation of concerns** - workflow logic separate from infrastructure concerns
4. **Backward compatible** - existing stage-based configurations continue to work
5. **Progressive complexity** - simple stage mappings initially, conditional logic later

This architecture maintains your existing stateless execution model while providing the higher-level abstractions developers need for complex agent behaviors.




## Architectural Decisions not Reviewed
- Logging
- Docker
- .env credential interpolation
- `ConversationHistory` data schema
- `MetricsCollector` and telemetry
- `core` versus `community` plugin separation- Import paths / circular imports
