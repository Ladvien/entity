# Architecture Decisions Summary

The following architecture decisions were made through systematic analysis of the Entity Pipeline Framework to optimize for developer adoption, scalability, and maintainability.

- [Architecture Decisions Summary](#architecture-decisions-summary)
  - [0. Folder Structure and Naming Conventions](#0-folder-structure-and-naming-conventions)
  - [Repository Layout](#repository-layout)
  - [1. Core Mental Model: Plugin Taxonomy and Architecture](#1-core-mental-model-plugin-taxonomy-and-architecture)
    - [**Plugin Categories**](#plugin-categories)
      - [**Infrastructure Plugins (ResourcePlugin)**](#infrastructure-plugins-resourceplugin)
      - [**Processing Plugins (Execution Plugins)**](#processing-plugins-execution-plugins)
      - [**Interface Plugins (AdapterPlugin)**](#interface-plugins-adapterplugin)
      - [**Specialized Plugins**](#specialized-plugins)
    - [**Resource Composition Architecture**](#resource-composition-architecture)
      - [**Required Resources**](#required-resources)
      - [**Composition Rules**](#composition-rules)
    - [**Plugin Lifecycle Management**](#plugin-lifecycle-management)
      - [**Two-Phase Lifecycle**](#two-phase-lifecycle)
      - [**Lifecycle Characteristics**](#lifecycle-characteristics)
    - [**Plugin Development Patterns**](#plugin-development-patterns)
      - [**Stage Assignment Precedence**](#stage-assignment-precedence)
      - [**Dependency Declaration**](#dependency-declaration)
      - [**Plugin Registration Order**](#plugin-registration-order)
    - [**Benefits of Unified Plugin Architecture**](#benefits-of-unified-plugin-architecture)
    - [**Plugin Validation and Discovery**](#plugin-validation-and-discovery)
  - [2. Progressive Disclosure: Enhanced 3-Layer Plugin System](#2-progressive-disclosure-enhanced-3-layer-plugin-system)
  - [3. Resource Management: Core Canonical + Simple Flexible Keys](#3-resource-management-core-canonical--simple-flexible-keys)
  - [4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults](#4-plugin-stage-assignment-guided-explicit-declaration-with-smart-defaults)
  - [5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation](#5-error-handling-and-validation-fail-fast-with-multi-layered-validation)
  - [7. Response Termination Control](#7-response-termination-control)
  - [8. Stage Results Accumulation Pattern](#8-stage-results-accumulation-pattern)
  - [9. Tool Execution Patterns](#9-tool-execution-patterns)
  - [10. Memory Resource Consolidation](#10-memory-resource-consolidation)
  - [11. Resource Dependency Injection Pattern](#11-resource-dependency-injection-pattern)
  - [12. Plugin Stage Assignment Precedence](#12-plugin-stage-assignment-precedence)
  - [13. Resource Lifecycle Management](#13-resource-lifecycle-management)
  - [14. Configuration Hot-Reload Scope](#14-configuration-hot-reload-scope)
  - [15. Error Handling and Failure Propagation](#15-error-handling-and-failure-propagation)
  - [16. Pipeline State Management Strategy](#16-pipeline-state-management-strategy)
  - [17. Plugin Execution Order Simplification](#17-plugin-execution-order-simplification)
  - [18. Configuration Validation Consolidation](#18-configuration-validation-consolidation)
  - [Summary So Far ✅](#summary-so-far-)
  - [19. Reasoning Pattern Abstraction Strategy](#19-reasoning-pattern-abstraction-strategy)
  - [20. Memory Architecture: Primitive Resources + Custom Plugins](#20-memory-architecture-primitive-resources--custom-plugins)
  - [21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration](#21-tool-discovery-architecture-lightweight-registry-query--plugin-level-orchestration)
  - [22. Plugin System Architecture: Explicit Configuration with Smart Defaults](#22-plugin-system-architecture-explicit-configuration-with-smart-defaults)
    - [Rationale](#rationale)
    - [Implementation Pattern](#implementation-pattern)
    - [Key Principles](#key-principles)
  - [23. State Management Consolidation: Unified Cache/Memory Pattern](#23-state-management-consolidation-unified-cachememory-pattern)
    - [Rationale](#rationale-1)
    - [Unified API Pattern](#unified-api-pattern)
    - [Key Principles](#key-principles-1)
  - [24. Agent Instantiation Unification: Single Agent Class Pattern](#24-agent-instantiation-unification-single-agent-class-pattern)
    - [Rationale](#rationale-2)
    - [Unified API Pattern](#unified-api-pattern-1)
    - [Key Principles](#key-principles-2)
  - [25. Workflow Objects with Progressive Complexity](#25-workflow-objects-with-progressive-complexity)
  - [26. Workflow Objects: Composable Agent Blueprints](#26-workflow-objects-composable-agent-blueprints)
  - [27. Layer 0: Zero-Config Developer Experience](#27-layer-0-zero-config-developer-experience)
  - [28. Infrastructure Components: Docker + OpenTofu Architecture](#28-infrastructure-components-docker--opentofu-architecture)
  - [29. Multi-User Support: user\_id Parameter Pattern](#29-multi-user-support-user_id-parameter-pattern)
  - [30. LoggingResource: Unified Agent Component Logging](#30-loggingresource-unified-agent-component-logging)
  - [31. MetricsCollectorResource: Shared Performance Tracking](#31-metricscollectorresource-shared-performance-tracking)
  - [Architectural Decisions not Reviewed](#architectural-decisions-not-reviewed)

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
- **Layer 0**: Zero-config quick start (see [Layer 0: Zero-Config Developer Experience](#27-layer-0-zero-config-developer-experience))
- **Layer 1**: Function decorators (`@agent.plugin`) with auto-classification
- **Layer 2**: Class-based plugins with explicit control
- **Layer 3**: Advanced plugins with sophisticated pipeline access

**Enhancements**:
- Automated upgrade suggestions when functions become complex
- Template generators via CLI: `poetry run entity-cli plugin generate my_function --type prompt`
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

-**2. Interactive Stage Discovery**:
- CLI command: `poetry run python src/cli/plugin_tool/main.py analyze-plugin my_plugin.py`
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
- CLI validation tools: `poetry run entity-cli validate --config config.yaml`
- Dependency graph visualization: `poetry run entity-cli workflow visualize config.yaml`
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
Implemented in `src/entity/worker/pipeline_worker.py`.

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



## 7. Response Termination Control

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
 - Earlier stages use `context.store()` to cache intermediate outputs for DELIVER plugins to access
- Maximum iteration limit (default 5) prevents infinite loops when no DELIVER plugin sets a response

**Benefits**: Ensures consistent output processing, logging, and formatting while maintaining the hybrid pipeline-state machine mental model.

## 8. Stage Results Accumulation Pattern

**Decision**: Use stage results accumulation with `context.store()`, `context.load()`, and `context.has()` methods for inter-stage communication.

**Rationale**:
- Builds on existing stage results infrastructure with intuitive naming
- Maintains pipeline mental model where each stage produces discrete outputs
- Stage results persist across pipeline iterations, enabling context accumulation
- Provides explicit traceability for debugging and observability
- Allows flexible composition patterns in DELIVER plugins

-**Implementation**:
- Earlier stages use `context.store(key, value)` to save intermediate outputs
- DELIVER plugins use `context.load(key)` to access stored results for response composition
- `context.has(key)` enables conditional logic based on available results
- Stage results are cleared between separate pipeline executions but persist across iterations within the same execution

**Benefits**: Clear data flow, debugging visibility, flexible response composition, and natural support for iterative pipeline execution.

## 9. Tool Execution Patterns

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
 
## 10. Memory Resource Consolidation

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


## 11. Resource Dependency Injection Pattern

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

## 12. Plugin Stage Assignment Precedence

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

## 13. Resource Lifecycle Management

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

## 14. Configuration Hot-Reload Scope

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

## 15. Error Handling and Failure Propagation

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

## 16. Pipeline State Management Strategy

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

## 17. Plugin Execution Order Simplification

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

## 19. Reasoning Pattern Abstraction Strategy

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

## 20. Memory Architecture: Primitive Resources + Custom Plugins

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

## 21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration

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
 - Four overlapping storage mechanisms (`context.store()`, `context.set_metadata()`, `memory.remember()`, conversation history)
- Unclear boundaries between temporary vs persistent data
- Data duplication with conversation history in multiple locations
- High cognitive overhead deciding which storage method to use

### Unified API Pattern

```python
# In PluginContext - simple, intuitive verbs:
context.store("analysis", result)     # Temporary data (dies with pipeline run)
context.load("analysis")              # Retrieve temporary data

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

## 27. Layer 0: Zero-Config Developer Experience

**Decision**: Implement a "Layer 0" that provides immediate functionality with zero configuration, using local-first resources and decorator-based auto-magic patterns.

**Core Purpose:**
- **Instant gratification**: Functional AI agents with 2-3 lines of code
- **Local-first development**: No API keys, accounts, or external dependencies required
- **Real AI responses**: Actual LLM inference using Ollama, not mock/echo responses
- **Friction-free onboarding**: Target "working in 5 minutes" developer experience
- **Progressive disclosure**: Natural graduation path to advanced framework features

**How it works:**
```python
# Zero configuration required
from entity import agent

@agent.tool
def calculator(expression: str) -> float:
    return eval(expression)

@agent.prompt  
def summarizer(text: str) -> str:
    return f"Summarize this text: {text}"  # LLM automatically called

# Agent works immediately
response = agent.chat("What's 15*23? Also summarize this article...")
```

**Default Resource Stack:**

**1. Ollama LLM Resource (Local AI)**
```python
# Auto-configured defaults
{
    "base_url": "http://localhost:11434",
    "model": "llama3.2:3b",              # Balance of speed/capability
    "temperature": 0.7,
    "timeout": 30,
    "retries": 3,
    "stream": False
}

# Model selection priority
preferred_models = [
    "llama3.2:3b",      # Primary: fast, capable, fits most hardware
    "llama3.2:1b",      # Fallback: lower-end hardware
    "phi3:mini",        # Alternative: Microsoft efficient model
    "gemma2:2b",        # Alternative: Google efficient model
]
```

**2. DuckDB Memory Resource (Embedded Database)**
```python
# Auto-configured defaults
{
    "path": "./agent_memory.duckdb",     # Local file, zero setup
    "memory_limit": "1GB",
    "threads": 4,
    "conversation_table": "conversations",
    "vector_table": "embeddings", 
    "vector_dimensions": 384,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**3. LocalFileSystem Storage Resource**
```python
# Auto-configured defaults
{
    "base_path": "./agent_files",
    "auto_create_dirs": True,
    "max_file_size": "10MB",
    "allowed_extensions": [".txt", ".json", ".csv", ".md", ".yaml", ".yml", ".log"],
    "backup_on_overwrite": True
}
```

**Implementation Patterns:**

**1. Auto-Registration Decorators**
- `@agent.tool` functions auto-register to DO stage
- `@agent.prompt` functions auto-register to THINK stage with LLM integration
- Functions automatically added to global agent instance
- No explicit plugin class creation required

**2. Auto-LLM Integration**
- Functions decorated with `@agent.prompt` automatically call LLM
- Return strings treated as prompts sent to Ollama
- LLM response becomes function's actual return value
- Eliminates manual `await context.call_llm()` boilerplate

**3. Implicit Resource Access**
```python
@agent.prompt
def contextual_chat(message: str, context) -> str:
    # Context parameter triggers auto-injection
    history = context.memory.get("chat_history", [])
    context.memory.remember("last_interaction", message)
    return f"Given conversation history {history}, respond to: {message}"
```

**Graceful Setup Experience:**

**Auto-Discovery and Setup**
```python
class Layer0SetupManager:
    def ensure_ollama(self):
        # 1. Check Ollama accessibility at localhost:11434
        # 2. Verify at least one model available
        # 3. If missing: provide installation instructions
        # 4. Auto-suggest: ollama pull llama3.2:3b
        
    def setup_resources(self):
        # 1. Create ./agent_memory.duckdb if missing
        # 2. Create ./agent_files/ directory structure
        # 3. Initialize conversation/vector tables in DuckDB
        # 4. Download embedding model for semantic search
```

**Error Handling Strategy**
- **Ollama unavailable**: Clear setup instructions with download links
- **No models installed**: Specific command suggestions (`ollama pull llama3.2:3b`)
- **Resource creation fails**: Graceful fallback to in-memory alternatives
- **Always actionable**: Every error includes specific next steps

**Progressive Disclosure Integration:**
```python
# Layer 0: Zero config
@agent.prompt
def chat(message: str) -> str:
    return f"Respond to: {message}"

# Layer 1: Add configuration
@agent.prompt(temperature=0.1, max_tokens=100)
def precise_chat(message: str) -> str:
    return f"Respond precisely to: {message}"

# Layer 2: Access context/resources
@agent.prompt
def memory_chat(message: str, context) -> str:
    context.memory.remember("topic", extract_topic(message))
    return f"Respond to: {message}"

# Layer 3: Full plugin classes
class AdvancedChatPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    dependencies = ["llm", "memory", "vector_store"]
```

**Key Design Principles:**
1. **Local-first architecture** - works offline, no external services required
2. **Real AI immediately** - actual LLM responses, not mock/echo behavior
3. **Zero configuration burden** - sensible defaults for everything
4. **Decorator-based simplicity** - familiar Python patterns, minimal learning curve
5. **Auto-magic with escape hatches** - magic behavior with clear upgrade paths
6. **Resource abstraction** - hide complexity while maintaining full power

**Benefits:**
- **Privacy by default**: Data never leaves user's machine during development
- **Cost-free experimentation**: No API billing concerns for learning/testing
- **Offline development**: Works without internet connectivity
- **Educational value**: Users learn local AI deployment patterns
- **Production graduation**: Easy scaling to cloud resources when needed

This Layer 0 positions the framework as the **"local-first AI agent framework"** while maintaining full architectural compatibility with enterprise-scale deployments through existing progressive disclosure layers.

Perfect! OpenTofu + Terragrunt + extensible templates through plugins - that's a much more robust and future-proof approach. Let me design this architecture.

## 28. Infrastructure Components: Docker + OpenTofu Architecture

**Decision**: Implement Infrastructure as composable components using Docker for local development and OpenTofu with Terragrunt for cloud deployment, with extensible template system via InfrastructurePlugins.

**Core Purpose:**
- **Consistent deployment pipeline**: Same agent config from laptop to production
- **Local development**: Docker for fast iteration and testing
- **Cloud deployment**: OpenTofu + Terragrunt for robust, reproducible infrastructure
- **Extensible templates**: InfrastructurePlugin system for custom deployment patterns
- **Zero infrastructure knowledge required**: Developers focus on agent logic, not DevOps

**How it works:**
```python
# Same agent config everywhere
agent = Agent.from_config("agent.yaml")

# Local development
docker_infra = DockerInfrastructure()
await docker_infra.deploy(agent)

# Production deployment (same agent)
aws_infra = AWSStandardInfrastructure()
await aws_infra.deploy(agent)

# Custom infrastructure via plugins
custom_infra = CustomInfrastructurePlugin("my-company-template")
await custom_infra.deploy(agent)
```

**Infrastructure Component Architecture:**

**1. Base Infrastructure Plugin Interface**
```python
class InfrastructurePlugin(ABC):
    """Base class for all infrastructure providers"""
    
    name: str
    provider: str  # aws, gcp, azure, docker, kubernetes
    
    @abstractmethod
    async def deploy(self, agent: Agent) -> DeploymentResult:
        """Deploy agent using this infrastructure"""
        
    @abstractmethod
    async def destroy(self) -> None:
        """Clean up all infrastructure resources"""
        
    @abstractmethod
    def generate_config(self, agent: Agent) -> InfrastructureConfig:
        """Generate infrastructure-specific configuration"""
        
    @abstractmethod
    def validate_requirements(self, agent: Agent) -> ValidationResult:
        """Validate agent config is compatible with this infrastructure"""
```

**2. Docker Infrastructure Plugin (Local Development)**
```python
class DockerInfrastructure(InfrastructurePlugin):
    """Docker-based local development with full service simulation"""
    
    name = "docker-local"
    provider = "docker"
    
    def __init__(self, profile: str = "development"):
        self.profile = profile
        self.services = {}
        self.compose_config = None
    
    async def deploy(self, agent: Agent) -> DeploymentResult:
        # 1. Analyze agent config for required services
        required_services = self._extract_services(agent.config)
        
        # 2. Generate docker-compose with service simulation
        self.compose_config = self._generate_compose_file(required_services, agent)
        
        # 3. Write compose file and Dockerfile
        self._write_docker_files(agent)
        
        # 4. Build agent container
        await self._build_agent_container(agent)
        
        # 5. Start infrastructure services with health checks
        await self._start_infrastructure_services()
        
        # 6. Start agent container
        await self._start_agent_container()
        
        return DeploymentResult(
            endpoint="http://localhost:8000",
            admin_dashboard="http://localhost:8001",
            services=list(self.services.keys()),
            logs_command="docker compose logs -f",
            metrics_endpoint="http://localhost:3000"  # Grafana
        )
    
    def _generate_compose_file(self, services: List[str], agent: Agent) -> Dict:
        """Generate docker-compose.yml with all required services"""
        
        compose = {
            "version": "3.8",
            "services": {},
            "volumes": {
                "agent_data": {},
                "ollama_data": {},
                "postgres_data": {},
                "minio_data": {},
                "grafana_data": {}
            },
            "networks": {
                "agent_network": {"driver": "bridge"}
            }
        }
        
        # Ollama service (if LLM resource needed)
        if self._needs_llm_service(agent.config):
            compose["services"]["ollama"] = {
                "image": "ollama/ollama:latest",
                "container_name": "agent-ollama",
                "ports": ["11434:11434"],
                "volumes": ["ollama_data:/root/.ollama"],
                "networks": ["agent_network"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost:11434/api/tags"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 5,
                    "start_period": "30s"
                },
                "restart": "unless-stopped"
            }
        
        # PostgreSQL service (if SQL database needed)
        if self._needs_sql_database(agent.config):
            compose["services"]["postgres"] = {
                "image": "postgres:15-alpine",
                "container_name": "agent-postgres", 
                "environment": {
                    "POSTGRES_DB": "agent_db",
                    "POSTGRES_USER": "agent_user",
                    "POSTGRES_PASSWORD": "dev_password_123"
                },
                "ports": ["5432:5432"],
                "volumes": [
                    "postgres_data:/var/lib/postgresql/data",
                    "./infrastructure/docker/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql"
                ],
                "networks": ["agent_network"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U agent_user -d agent_db"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5
                }
            }
        
        # MinIO service (S3-compatible storage)
        if self._needs_object_storage(agent.config):
            compose["services"]["minio"] = {
                "image": "minio/minio:latest",
                "container_name": "agent-minio",
                "command": "server /data --console-address ':9001'",
                "environment": {
                    "MINIO_ROOT_USER": "minioadmin",
                    "MINIO_ROOT_PASSWORD": "minioadmin123"
                },
                "ports": ["9000:9000", "9001:9001"],
                "volumes": ["minio_data:/data"],
                "networks": ["agent_network"],
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"],
                    "interval": "10s",
                    "timeout": "3s",
                    "retries": 3
                }
            }
        
        # Observability stack
        if self.profile in ["development", "testing"]:
            self._add_observability_services(compose)
        
        # Main agent service
        compose["services"]["agent"] = {
            "build": {
                "context": ".",
                "dockerfile": "Dockerfile"
            },
            "container_name": "agent-main",
            "depends_on": {
                service: {"condition": "service_healthy"} 
                for service in compose["services"].keys()
            },
            "environment": self._generate_agent_env_vars(agent.config),
            "ports": ["8000:8000"],
            "volumes": ["agent_data:/app/data"],
            "networks": ["agent_network"],
            "restart": "unless-stopped"
        }
        
        return compose
```

**3. OpenTofu Infrastructure Plugins (Cloud Deployment)**
```python
class OpenTofuInfrastructure(InfrastructurePlugin):
    """Base class for OpenTofu-based cloud infrastructure"""
    
    def __init__(self, 
                 provider: str,
                 template: str,
                 region: str = "us-east-1"):
        self.provider = provider
        self.template = template
        self.region = region
        self.terragrunt_config = None
        self.tofu_modules = {}
    
    async def deploy(self, agent: Agent) -> DeploymentResult:
        # 1. Generate Terragrunt configuration
        self.terragrunt_config = self._generate_terragrunt_config(agent)
        
        # 2. Create OpenTofu modules
        self.tofu_modules = self._generate_tofu_modules(agent.config)
        
        # 3. Write infrastructure files
        self._write_infrastructure_files(agent)
        
        # 4. Build and push agent container to registry
        image_uri = await self._build_and_push_agent_image(agent)
        
        # 5. Deploy infrastructure with Terragrunt
        result = await self._run_terragrunt_deploy(image_uri)
        
        return result

class AWSStandardInfrastructure(OpenTofuInfrastructure):
    """Standard AWS deployment: ECS + RDS + S3 + ALB"""
    
    name = "aws-standard"
    provider = "aws"
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__("aws", "standard", region)
    
    def _generate_tofu_modules(self, agent_config: Dict) -> Dict[str, str]:
        """Generate OpenTofu modules for standard AWS deployment"""
        
        return {
            # Core networking
            "vpc": self._generate_vpc_module(),
            
            # Container infrastructure
            "ecr": self._generate_ecr_module(),
            "ecs": self._generate_ecs_module(agent_config),
            "load_balancer": self._generate_alb_module(),
            
            # Data services
            "rds": self._generate_rds_module(agent_config),
            "s3": self._generate_s3_module(agent_config),
            
            # Security
            "iam": self._generate_iam_module(),
            "security_groups": self._generate_security_groups_module(),
            
            # Observability
            "cloudwatch": self._generate_cloudwatch_module(),
            "logs": self._generate_logs_module()
        }
    
    def _generate_ecs_module(self, agent_config: Dict) -> str:
        """Generate ECS service configuration"""
        
        # Determine resource requirements based on agent config
        cpu_units, memory_mb = self._calculate_resource_requirements(agent_config)
        
        return f"""
        module "ecs_service" {{
          source = "terraform-aws-modules/ecs/aws//modules/service"
          version = "~> 5.0"
          
          name = "agent-{agent_config['name']}"
          cluster_arn = module.ecs_cluster.cluster_arn
          
          cpu    = {cpu_units}
          memory = {memory_mb}
          
          container_definitions = {{
            agent = {{
              image = var.agent_image_uri
              port_mappings = [{{
                name          = "agent-http"
                containerPort = 8000
                protocol      = "tcp"
              }}]
              
              environment = [
                {{
                  name  = "DATABASE_URL"
                  value = module.rds.db_instance_endpoint
                }},
                {{
                  name  = "S3_BUCKET"
                  value = module.s3.s3_bucket_id
                }},
                # ... more environment variables
              ]
              
              secrets = [
                {{
                  name      = "DB_PASSWORD"
                  valueFrom = module.rds.db_instance_master_user_secret_arn
                }}
              ]
              
              log_configuration = {{
                log_driver = "awslogs"
                log_group  = module.logs.cloudwatch_log_group_name
              }}
            }}
          }}
          
          load_balancer = {{
            service = {{
              target_group_arn = module.load_balancer.target_groups["agent"].arn
              container_name   = "agent"
              container_port   = 8000
            }}
          }}
          
          subnet_ids = module.vpc.private_subnets
          security_group_ids = [module.security_groups.agent_sg_id]
        }}
        """

class AWSGPUInfrastructure(OpenTofuInfrastructure):
    """GPU-enabled AWS deployment for local LLM inference"""
    
    name = "aws-gpu-enabled" 
    provider = "aws"
    
    def _generate_tofu_modules(self, agent_config: Dict) -> Dict[str, str]:
        """Generate OpenTofu modules for GPU-enabled deployment"""
        
        modules = super()._generate_tofu_modules(agent_config)
        
        # Replace ECS with EC2 GPU instances
        del modules["ecs"]
        modules["ec2_gpu"] = self._generate_gpu_ec2_module(agent_config)
        modules["auto_scaling"] = self._generate_asg_module()
        
        return modules

class CustomInfrastructurePlugin(InfrastructurePlugin):
    """User-defined infrastructure plugin loaded from external modules"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template_module = self._load_template_module()
    
    def _load_template_module(self):
        """Load custom infrastructure template from user-defined module"""
        # Import user's custom infrastructure definition
        # Support both Python modules and declarative YAML/JSON
        pass
```

**CLI Integration:**
```bash
# Local development
entity-cli infra init docker --profile development
entity-cli infra deploy --local
entity-cli infra logs --service ollama
entity-cli infra destroy --local

# Cloud deployment
entity-cli infra init aws-standard --region us-east-1
entity-cli infra plan --cloud                    # OpenTofu plan
entity-cli infra deploy --cloud                  # Terragrunt apply
entity-cli infra status --cloud                  # Check deployment status
entity-cli infra destroy --cloud --auto-approve  # Clean up

# Custom infrastructure
entity-cli infra init custom --template ./my-company/k8s-template
entity-cli infra deploy --template my-company-k8s

# Workflow: Test locally → Deploy to cloud
entity-cli infra test --local                    # Test with Docker
entity-cli infra migrate --from docker --to aws-standard  # Deploy same config
```

**Key Design Principles:**
1. **OpenTofu + Terragrunt**: Modern, open-source infrastructure as code
2. **Automatic ECR management**: Framework creates and manages container registries
3. **Template extensibility**: InfrastructurePlugin system for custom deployments
4. **Environment parity**: Same agent config works across all infrastructure
5. **Zero DevOps knowledge**: Developers focus on agent logic, infrastructure is automated
6. **Production ready**: Built-in observability, security, and scalability

This architecture gives you **"commit to production"** - developers can test locally with Docker, then deploy to AWS with a single command using battle-tested OpenTofu modules.

## 29. Multi-User Support: user_id Parameter Pattern

**Decision**: Implement multi-user support through a simple `user_id` parameter in pipeline execution, using conversation namespacing for user isolation.

**Core Purpose:**
- **User isolation**: Separate conversation state per user within same agent instance
- **Resource efficiency**: Share agent logic and resources across users
- **Simplicity**: Minimal architectural complexity with maximum functionality
- **Clear security model**: Different user bases use separate deployments

**How it works:**
```python
# Same agent instance handles multiple users
agent = Agent.from_config("support-bot.yaml")

# User 1's conversation
response1 = await agent.chat("Hello, I need help", user_id="user123")

# User 2's conversation (completely isolated)
response2 = await agent.chat("Hi there", user_id="user456") 

# User 1 continues their conversation
response3 = await agent.chat("Thanks for the help", user_id="user123")
```

**Implementation Pattern:**

**Pipeline Execution Signature**
```python
async def execute_pipeline(
    user_message: str,
    capabilities: SystemRegistries,
    *,
    user_id: str,                    # User identifier for conversation isolation
    state_logger: StateLogger | None = None,
    return_metrics: bool = False,
    state: PipelineState | None = None,
    max_iterations: int = 5,
) -> Dict[str, Any] | tuple[Dict[str, Any], MetricsCollector]:
```

**Memory Resource Integration**
```python
class Memory(ResourcePlugin):
    async def save_conversation(self, conversation_id: str, history: List[ConversationEntry]) -> None:
        # conversation_id format: "{user_id}_{pipeline_id}"
        self._conversations[conversation_id] = list(history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        # Automatic user isolation through namespaced conversation_id
        return list(self._conversations.get(conversation_id, []))
        
    def remember(self, key: str, value: Any) -> None:
        """Store user-specific persistent data with automatic namespacing"""
        # Key automatically includes user context when called from pipeline
        self._kv[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve user-specific persistent data"""
        return self._kv.get(key, default)
```

**Agent-Level API**
```python
class Agent:
    async def chat(self, message: str, *, user_id: str) -> Dict[str, Any]:
        """Chat with the agent using user-specific conversation context"""
        return await self.run_message(message, user_id=user_id)
        
    async def run_message(self, message: str, *, user_id: str) -> Dict[str, Any]:
        """Run message through the runtime pipeline with user isolation"""
        await self._ensure_runtime()
        if self._runtime is None:
            raise RuntimeError("Runtime not initialized")
        
        # Create user-specific pipeline_id
        pipeline_id = f"{user_id}_{generate_pipeline_id()}"
        
        # Load user's conversation history
        memory = self._runtime.capabilities.resources.get("memory")
        conversation_history = await memory.load_conversation(pipeline_id)
        
        # Create pipeline state with user context
        state = PipelineState(
            conversation=conversation_history + [ConversationEntry(
                content=message, 
                role="user", 
                timestamp=datetime.now()
            )],
            pipeline_id=pipeline_id,
            metrics=MetricsCollector(),
        )
        
        # Execute pipeline
        result = await execute_pipeline(
            message, 
            self._runtime.capabilities,
            user_id=user_id,
            state=state
        )
        
        # Save updated conversation
        await memory.save_conversation(pipeline_id, state.conversation)
        
        return result
```

**PluginContext Integration**
```python
class PluginContext:
    def __init__(self, state: PipelineState, registries: Any, user_id: str) -> None:
        self._state = state
        self._registries = registries
        self._user_id = user_id
        self._memory = getattr(registries.resources, "memory", None)

    @property
    def user_id(self) -> str:
        """Get the current user ID for this pipeline execution"""
        return self._user_id

    def remember(self, key: str, value: Any) -> None:
        """Persist user-specific value in the configured memory resource"""
        if self._memory is not None:
            # Automatically namespace key with user_id
            namespaced_key = f"{self._user_id}:{key}"
            self._memory.remember(namespaced_key, value)

    def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve user-specific value from persistent memory"""
        if self._memory is None:
            return default
        namespaced_key = f"{self._user_id}:{key}"
        return self._memory.get(namespaced_key, default)
```

**User Isolation Strategy:**
- **Conversation namespacing**: `pipeline_id = f"{user_id}_{generate_pipeline_id()}"`
- **Memory isolation**: Memory keys automatically prefixed with `user_id:`
- **Shared resources**: LLM, tools, and plugin logic shared across users
- **No cross-user data leakage**: User isolation enforced at memory and context layers

**Deployment Patterns:**

**Single Organization Multi-User**
```python
# One agent instance serves multiple users within organization
agent = Agent.from_config("company-assistant.yaml")
# Users: employee1, employee2, employee3, etc.
```

**Multi-Organization Isolation**
```python
# Separate deployments for different organizations
customer_a_agent = Agent.from_config("customer-a-config.yaml")
customer_b_agent = Agent.from_config("customer-b-config.yaml")
# Complete separation for security and customization
```

**Key Design Principles:**
1. **Minimal complexity**: Single parameter addition to existing architecture
2. **Natural isolation**: user_id becomes conversation and memory namespace
3. **Resource sharing**: Efficient use of LLM and infrastructure resources
4. **Clear boundaries**: Different user bases require separate deployments
5. **Zero overhead**: No runtime performance impact for user isolation
6. **Backward compatibility**: Existing single-user agents continue working

**Benefits:**
- **Cost efficiency**: Multiple users share same agent infrastructure
- **Simple scaling**: Add more users until resource limits, then scale instances
- **Security by design**: User data automatically isolated through namespacing
- **Operational simplicity**: No complex multi-tenant management required
- **Clear upgrade path**: Easy to move users to dedicated instances if needed

This pattern provides robust multi-user support with essentially zero architectural overhead while maintaining clear security boundaries and operational simplicity.

## 30. LoggingResource: Unified Agent Component Logging

**Decision**: Implement a `LoggingResource` that provides unified, multi-output logging for all agent components with real-time streaming capabilities.

**Core Purpose:**
- **Unified logging interface**: Single logging API for all plugins, resources, and pipeline stages
- **Multi-output support**: Simultaneous logging to console, files, and real-time streams
- **Component traceability**: Track log entries across plugins, stages, and resource operations
- **Real-time monitoring**: WebSocket streaming for live dashboards and debugging
- **Zero dependencies**: Critical infrastructure that must always function

**How it works:**
```python
# All components use the same logging interface
logger = context.get_resource("logging")

await logger.log("info", "Plugin execution started",
                 component="plugin",
                 user_id=context.user_id,
                 pipeline_id=context.pipeline_id,
                 stage=context.current_stage,
                 plugin_name=self.__class__.__name__)
```

**Implementation Architecture:**

**LoggingResource Base**
```python
class LoggingResource(ResourcePlugin):
    """Unified logging for all agent components with multi-output support"""
    
    name = "logging"
    dependencies = []  # Critical: logging must never depend on other resources
    
    async def log(self, 
                  level: str, 
                  message: str, 
                  *, 
                  component: str,           # "plugin", "resource", "pipeline", "tool"
                  user_id: str | None = None,
                  pipeline_id: str | None = None,
                  stage: PipelineStage | None = None,
                  plugin_name: str | None = None,
                  resource_name: str | None = None,
                  **extra_context) -> None:
        """Send log entry to all configured outputs simultaneously"""
```

**Multi-Output System**
```python
class LogOutput(ABC):
    """Base class for logging destinations"""
    
    @abstractmethod
    async def write(self, entry: LogEntry) -> None:
        """Write log entry to destination"""

# Simultaneous outputs
outputs = [
    ConsoleLogOutput(),           # Human-readable console
    StructuredFileOutput(),       # JSON Lines for analysis
    RealTimeStreamOutput(),       # WebSocket for dashboards
    ElasticsearchOutput(),        # Optional: centralized logging
]
```

**Automatic Integration Points:**

**Plugin Execution Logging**
```python
# Automatic wrapping in BasePlugin.execute()
async def execute(self, context: PluginContext) -> Any:
    logger = context.get_resource("logging")
    
    await logger.log("info", f"Plugin {self.__class__.__name__} starting",
                     component="plugin",
                     user_id=context.user_id,
                     pipeline_id=context.pipeline_id,
                     stage=context.current_stage,
                     plugin_name=self.__class__.__name__)
    
    start_time = time.perf_counter()
    try:
        result = await self._execute_impl(context)
        duration = time.perf_counter() - start_time
        
        await logger.log("info", f"Plugin completed successfully",
                         component="plugin",
                         duration_ms=duration * 1000,
                         success=True,
                         **context_info)
        return result
    except Exception as e:
        await logger.log("error", f"Plugin failed: {str(e)}",
                         component="plugin",
                         duration_ms=(time.perf_counter() - start_time) * 1000,
                         success=False,
                         error_type=e.__class__.__name__,
                         **context_info)
        raise
```

**Resource Operation Logging**
```python
# Automatic logging in resource operations
class LLMResource(ResourcePlugin):
    async def generate(self, prompt: str, context: PluginContext) -> LLMResponse:
        logger = context.get_resource("logging")
        
        await logger.log("debug", "LLM request initiated",
                         component="resource",
                         resource_name="llm",
                         user_id=context.user_id,
                         pipeline_id=context.pipeline_id,
                         prompt_length=len(prompt),
                         model=self.model_name)
        
        start_time = time.perf_counter()
        response = await self._actual_generate(prompt)
        duration = time.perf_counter() - start_time
        
        await logger.log("info", "LLM response completed",
                         component="resource",
                         resource_name="llm",
                         duration_ms=duration * 1000,
                         prompt_length=len(prompt),
                         response_length=len(response.content),
                         estimated_tokens=self._estimate_tokens(prompt, response))
        
        return response
```

**Configuration Pattern:**
```yaml
plugins:
  resources:
    logging:
      type: entity.resources.logging:LoggingResource
      outputs:
        - type: console
          level: info
          format: human_readable
          
        - type: structured_file
          level: debug
          path: ./logs/agent.jsonl
          max_size: "100MB"
          backup_count: 5
          rotation: daily
          
        - type: real_time_stream
          level: info
          websocket_port: 8001
          max_clients: 50
          
      context_enrichment:
        include_hostname: true
        include_process_id: true
        correlation_header: "X-Trace-ID"
        
      filters:
        - component: resource
          resource_name: llm
          min_level: debug
        - component: plugin
          min_level: info
```

**Key Design Principles:**
1. **Zero dependencies**: Logging must work even if other resources fail
2. **Automatic integration**: Components get logging without manual setup
3. **Multi-output simultaneous**: Console + file + real-time + external systems
4. **Structured data**: Consistent fields for filtering and analysis
5. **Real-time streaming**: WebSocket support for live monitoring dashboards
6. **Context preservation**: Full traceability across pipeline execution

## 31. MetricsCollectorResource: Shared Performance Tracking

**Decision**: Implement `MetricsCollectorResource` as a shared resource automatically injected into all plugins, providing unified metrics collection across the entire agent execution.

**Core Purpose:**
- **Shared injection**: Automatically available to all plugins via dependency injection
- **Unified collection**: Single point for all agent metrics regardless of plugin type
- **Zero configuration**: Plugins get metrics collection without manual setup
- **Consistent data model**: Standardized metrics across all agent components
- **Centralized analytics**: Complete agent performance picture in one place

**How it works:**
```python
# Automatically injected into all plugins
class BasePlugin:
    dependencies = ["metrics_collector"]  # Automatic for all plugins
    
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.metrics_collector = None  # Injected by container
        
    async def execute(self, context: PluginContext) -> Any:
        # Automatic metric collection wrapper
        start_time = time.perf_counter()
        try:
            result = await self._execute_impl(context)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            await self.metrics_collector.record_plugin_execution(
                pipeline_id=context.pipeline_id,
                stage=context.current_stage,
                plugin_name=self.__class__.__name__,
                duration_ms=duration_ms,
                success=True
            )
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            await self.metrics_collector.record_plugin_execution(
                pipeline_id=context.pipeline_id,
                stage=context.current_stage,
                plugin_name=self.__class__.__name__,
                duration_ms=duration_ms,
                success=False,
                error_type=e.__class__.__name__
            )
            raise
```

**Plugin-Level Usage:**
```python
class MyPromptPlugin(PromptPlugin):
    # metrics_collector automatically injected
    
    async def _execute_impl(self, context: PluginContext) -> None:
        # Plugin can record custom metrics
        await self.metrics_collector.record_custom_metric(
            pipeline_id=context.pipeline_id,
            metric_name="prompt_complexity",
            value=self._calculate_complexity(context.message),
            metadata={"reasoning_type": "chain_of_thought"}
        )
        
        # Call LLM (metrics automatically collected)
        response = await self.call_llm(context, "Analyze this...", purpose="analysis")
        
        # Record business metric
        await self.metrics_collector.record_custom_metric(
            pipeline_id=context.pipeline_id,
            metric_name="analysis_confidence",
            value=self._extract_confidence(response.content)
        )
        
        context.say(response.content)

class WeatherToolPlugin(ToolPlugin):
    # metrics_collector automatically injected
    
    async def execute_function(self, params: Dict[str, Any]) -> Any:
        # Record tool-specific metrics
        await self.metrics_collector.record_custom_metric(
            pipeline_id=self._current_pipeline_id,  # Available via context
            metric_name="api_calls",
            value=1,
            metadata={
                "tool_name": "weather",
                "location": params.get("location"),
                "cache_hit": False
            }
        )
        
        return await self._fetch_weather(params["location"])
```

**MetricsCollectorResource Implementation:**
```python
class MetricsCollectorResource(ResourcePlugin):
    """Shared metrics collection resource injected into all plugins"""
    
    name = "metrics_collector"
    dependencies = ["database"]
    
    def __init__(self, config: Dict | None = None):
        super().__init__(config or {})
        self.database = None  # Injected by container
        self.active_pipelines = {}  # Real-time tracking
        self.metric_buffer = []  # Batch collection
        
    # Core collection methods used by framework
    async def record_plugin_execution(self,
                                    pipeline_id: str,
                                    stage: PipelineStage,
                                    plugin_name: str,
                                    duration_ms: float,
                                    success: bool,
                                    error_type: str = None) -> None:
        """Record plugin execution (called automatically by BasePlugin)"""
        
    async def record_resource_operation(self,
                                      pipeline_id: str,
                                      resource_name: str,
                                      operation: str,
                                      duration_ms: float,
                                      success: bool,
                                      metadata: Dict[str, Any] = None) -> None:
        """Record resource usage (called by resource wrappers)"""
        
    # Plugin-facing methods for custom metrics
    async def record_custom_metric(self,
                                 pipeline_id: str,
                                 metric_name: str,
                                 value: float,
                                 metadata: Dict[str, Any] = None) -> None:
        """Allow plugins to record domain-specific metrics"""
        
    async def increment_counter(self,
                              pipeline_id: str,
                              counter_name: str,
                              increment: int = 1,
                              metadata: Dict[str, Any] = None) -> None:
        """Increment a named counter (e.g., API calls, tool uses)"""
        
    # Analytics and querying
    async def get_unified_agent_log(self, 
                                   pipeline_id: str = None,
                                   user_id: str = None,
                                   time_range: tuple = None) -> List[Dict[str, Any]]:
        """Get complete unified log for agent execution"""
        
    async def get_performance_summary(self, agent_name: str, hours: int = 24) -> Dict[str, Any]:
        """Complete agent performance summary"""
```

**Automatic Dependency Injection:**
```python
# In SystemInitializer
class SystemInitializer:
    def _register_plugins(self):
        # Automatically add metrics_collector to all plugin dependencies
        for plugin_class in self.plugin_classes:
            if "metrics_collector" not in plugin_class.dependencies:
                plugin_class.dependencies.append("metrics_collector")
    
    async def initialize(self):
        # Ensure metrics_collector is always available
        if "metrics_collector" not in self.config["plugins"]["resources"]:
            self.config["plugins"]["resources"]["metrics_collector"] = {
                "type": "entity.resources.metrics_collector:MetricsCollectorResource"
            }
        
        # Standard initialization continues...
```

**Resource Operation Wrapping:**
```python
# All resources automatically track operations
class ResourcePlugin:
    dependencies = ["metrics_collector"]  # Automatic for all resources
    
    async def _track_operation(self, operation: str, func: Callable, context: PluginContext = None, **metadata):
        """Automatic operation tracking for all resources"""
        start_time = time.perf_counter()
        try:
            result = await func()
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            await self.metrics_collector.record_resource_operation(
                pipeline_id=context.pipeline_id if context else "system",
                resource_name=self.name,
                operation=operation,
                duration_ms=duration_ms,
                success=True,
                metadata=metadata
            )
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            await self.metrics_collector.record_resource_operation(
                pipeline_id=context.pipeline_id if context else "system",
                resource_name=self.name,
                operation=operation,
                duration_ms=duration_ms,
                success=False,
                metadata={**metadata, "error": str(e), "error_type": e.__class__.__name__}
            )
            raise

# LLM usage automatically tracked
class LLMResource(ResourcePlugin):
    async def generate(self, prompt: str, context: PluginContext) -> LLMResponse:
        return await self._track_operation(
            operation="generate",
            func=lambda: self._actual_generate(prompt),
            context=context,
            prompt_length=len(prompt),
            model=self.model_name,
            estimated_tokens=len(prompt.split())
        )
```

**Unified Agent Log Query:**
```python
# Get complete picture of agent execution
metrics = agent.get_resource("metrics_collector")

# Complete agent activity log
unified_log = await metrics.get_unified_agent_log(
    user_id="user123",
    time_range=(start_time, end_time)
)

# Results include:
# - Pipeline executions with stages
# - Plugin executions with performance
# - Resource operations with metadata  
# - Custom metrics from plugins
# - Error tracking and success rates
# - Complete traceability per user/pipeline
```

**Configuration (Minimal):**
```yaml
plugins:
  resources:
    # metrics_collector automatically added if not present
    metrics_collector:
      type: entity.resources.metrics_collector:MetricsCollectorResource
      # No explicit dependencies needed - auto-configured
      retention_days: 90
      buffer_size: 1000
```

**Key Benefits:**
1. **Zero plugin overhead**: Automatic injection, no manual setup required
2. **Unified data model**: All metrics flow through single collection point
3. **Complete agent visibility**: Every operation tracked automatically
4. **Custom metrics support**: Plugins can add domain-specific measurements
5. **Consistent performance data**: Same collection mechanism across all components
6. **Simplified analytics**: Single source of truth for agent performance

This approach creates a **unified agent execution log** where every operation, from high-level pipeline stages down to individual resource calls, flows through the same metrics collector. Plugin developers get rich metrics automatically while having the option to add custom business metrics as needed.


## Architectural Decisions not Reviewed
Future Features List

- Agent-to-Agent Communication Architecture - Multi-agent coordination, message buses, agent registries, and swarms
- Plugin Discovery and Distribution Architecture - Plugin registry, search, installation, versioning, and security validation
- Logging
- .env credential interpolation
- `MetricsCollector` and telemetry
- `core` versus `community` plugin separation
- Import paths / circular imports
