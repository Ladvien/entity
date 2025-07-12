# Architecture Decisions Summary

The following architecture decisions were made through systematic analysis of the Entity Pipeline Framework to optimize for developer adoption, scalability, and maintainability.

# Architecture Decisions Table of Contents
*Ordered by architectural impact (major → minor)*

## Core Foundational Architecture
- [1. Core Mental Model: Plugin Taxonomy and 4-Layer Resource Architecture](#1-core-mental-model-plugin-taxonomy-and-4-layer-resource-architecture)
  - [**Plugin Categories**](#plugin-categories)
    - [**Infrastructure Plugins (Layer 1 - No Dependencies)**](#infrastructure-plugins-layer-1---no-dependencies)
    - [**Resource Interface Plugins (Layer 2 - Depend Only on Layer 1)**](#resource-interface-plugins-layer-2---depend-only-on-layer-1)
    - [**Canonical Agent Resources (Layer 3 - Depend Only on Layer 2)**](#canonical-agent-resources-layer-3---depend-only-on-layer-2)
    - [**Processing Plugins (Execute During Pipeline Stages)**](#processing-plugins-execute-during-pipeline-stages)
    - [**Interface Plugins (AdapterPlugin)**](#interface-plugins-adapterplugin)
    - [**Specialized Plugins**](#specialized-plugins)
  - [**4-Layer Resource Architecture**](#4-layer-resource-architecture)
    - [**Required Resources (Layer 3 - Canonical)**](#required-resources-layer-3---canonical)
    - [**Custom Agent Resources (Layer 4 - User Compositions)**](#custom-agent-resources-layer-4---user-compositions)
    - [**Resource Composition Rules**](#resource-composition-rules)
    - [**Dependency Flow (Strict Hierarchy)**](#dependency-flow-strict-hierarchy)
  - [**Plugin Lifecycle Management**](#plugin-lifecycle-management)
  - [**Plugin Development Patterns**](#plugin-development-patterns)
  - [**Configuration Integration**](#configuration-integration)
  - [**Benefits of Unified Plugin + Resource Architecture**](#benefits-of-unified-plugin--resource-architecture)
  - [**Plugin Validation and Discovery**](#plugin-validation-and-discovery)

## Core Pipeline Architecture
- [6. Scalability Architecture: Persistent State with Stateless Workers](#6-scalability-architecture-persistent-state-with-stateless-workers)
- [4. Plugin Stage Assignment: Explicit Declaration with Simple Defaults](#4-plugin-stage-assignment-explicit-declaration-with-simple-defaults)
- [23. State Management Consolidation: Dual Interface Pattern](#23-state-management-consolidation-dual-interface-pattern)
  - [Rationale](#rationale-1)
  - [Dual Interface Pattern](#dual-interface-pattern)
  - [Key Principles](#key-principles-1)
  - [Implementation Architecture](#implementation-architecture)
- [7. Response Termination Control](#7-response-termination-control)
- [8. Stage Results Accumulation Pattern](#8-stage-results-accumulation-pattern)

## Core Resource Management
- [10. Memory Resource Consolidation](#10-memory-resource-consolidation)
- [3. Resource Management: Core Canonical + Simple Flexible Keys](#3-resource-management-core-canonical--simple-flexible-keys)
- [11. Resource Dependency Injection Pattern](#11-resource-dependency-injection-pattern)
- [13. Resource Lifecycle Management](#13-resource-lifecycle-management)

## Developer Experience & API Design
- [24. Agent Instantiation Unification: Single Agent Class Pattern](#24-agent-instantiation-unification-single-agent-class-pattern)
  - [Rationale](#rationale-2)
  - [Unified API Pattern](#unified-api-pattern)
  - [Key Principles](#key-principles-2)
- [27. Layer 0: Zero-Config Developer Experience](#27-layer-0-zero-config-developer-experience)
- [2. Progressive Disclosure: Enhanced 3-Layer Plugin System](#2-progressive-disclosure-enhanced-3-layer-plugin-system)
- [22. Plugin System Architecture: Explicit Configuration with Smart Defaults](#22-plugin-system-architecture-explicit-configuration-with-smart-defaults)
  - [Rationale](#rationale)
  - [Implementation Pattern](#implementation-pattern)
  - [Key Principles](#key-principles)

## Error Handling & Validation
- [5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation](#5-error-handling-and-validation-fail-fast-with-multi-layered-validation)
- [15. Error Handling and Failure Propagation](#15-error-handling-and-failure-propagation)
- [18. Configuration Validation Consolidation](#18-configuration-validation-consolidation)

## Workflow & Composition
- [25. Workflow Objects with Progressive Complexity](#25-workflow-objects-with-progressive-complexity)
- [26. Workflow Objects: Composable Agent Blueprints](#26-workflow-objects-composable-agent-blueprints)

## Infrastructure & Deployment
- [28. Infrastructure Components: Docker + OpenTofu Architecture](#28-infrastructure-components-docker--opentofu-architecture)
- [29. Multi-User Support: user_id Parameter Pattern](#29-multi-user-support-user_id-parameter-pattern)

## Observability & Monitoring
- [30. LoggingResource: Unified Agent Component Logging](#30-loggingresource-unified-agent-component-logging)
- [31. MetricsCollectorResource: Shared Performance Tracking](#31-metricscollectorresource-shared-performance-tracking)

## Specific Feature Patterns
- [19. Reasoning Pattern Abstraction Strategy](#19-reasoning-pattern-abstraction-strategy)
- [20. Memory Architecture: Primitive Resources + Custom Plugins](#20-memory-architecture-primitive-resources--custom-plugins)
- [21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration](#21-tool-discovery-architecture-lightweight-registry-query--plugin-level-orchestration)
- [9. Tool Execution Patterns](#9-tool-execution-patterns)

## Implementation Details & Minor Configuration
- [16. Pipeline State Management Strategy](#16-pipeline-state-management-strategy)
- [17. Plugin Execution Order Simplification](#17-plugin-execution-order-simplification)
- [14. Configuration Hot-Reload Scope](#14-configuration-hot-reload-scope)
- [0. Folder Structure and Naming Conventions](#0-folder-structure-and-naming-conventions)
  - [Repository Layout](#repository-layout)

## Future Considerations
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

# 1. Core Mental Model: Plugin Taxonomy and 4-Layer Resource Architecture

The Entity Pipeline Framework uses a unified plugin architecture where all extensions inherit from a single `Plugin` base class, combined with a strict 4-layer resource architecture that prevents circular dependencies through dependency inversion.

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

## **Plugin Categories**

### **Infrastructure Plugins (Layer 1 - No Dependencies)**
Concrete technology implementations that provide foundational capabilities. These are completely self-contained.

```python
class InfrastructurePlugin(Plugin):
    """Layer 1: Concrete technology implementations - NO DEPENDENCIES"""
    infrastructure_type: str  # "database", "vector_store", "llm_provider", "file_system"

class PostgresInfrastructure(InfrastructurePlugin):
    infrastructure_type = "database"
    # Examples: PostgresInfrastructure, DuckDBInfrastructure

class PgVectorInfrastructure(InfrastructurePlugin):
    infrastructure_type = "vector_store"
    # Examples: PgVectorInfrastructure, ChromaInfrastructure

class OllamaInfrastructure(InfrastructurePlugin):
    infrastructure_type = "llm_provider"
    # Examples: OllamaInfrastructure, OpenAIInfrastructure
```

### **Resource Interface Plugins (Layer 2 - Depend Only on Layer 1)**
Technology-agnostic interfaces that provide consistent APIs over infrastructure primitives.

```python
class ResourcePlugin(Plugin):
    """Layer 2: Abstract resource interfaces over infrastructure primitives"""
    infrastructure_dependencies: List[str] = []  # Required infrastructure_types

class DatabaseResource(ResourcePlugin):
    infrastructure_dependencies = ["database"]
    
    def __init__(self, postgres_infra: PostgresInfrastructure, config: Dict | None = None):
        # Constructor injection from Layer 1 only

class VectorStoreResource(ResourcePlugin):
    infrastructure_dependencies = ["vector_store"]
    
class LLMResource(ResourcePlugin):
    infrastructure_dependencies = ["llm_provider"]
```

### **Canonical Agent Resources (Layer 3 - Depend Only on Layer 2)**
Simple building blocks provided by the framework. These are the **guaranteed resources** available to all plugins.

```python
class AgentResource(ResourcePlugin):
    """Layer 3: Canonical building blocks - depend only on Layer 2"""

class Memory(AgentResource):
    """Canonical memory - simple building block with NO other agent resource dependencies"""
    
    def __init__(self, database: DatabaseResource, vector_store: VectorStoreResource, config: Dict | None = None):
        # Constructor injection from Layer 2 only - NO LLM dependency

class LLM(AgentResource):
    """Canonical LLM - simple building block with NO other agent resource dependencies"""
    
    def __init__(self, llm_resource: LLMResource, config: Dict | None = None):
        # Constructor injection from Layer 2 only

class Storage(AgentResource):
    """Canonical storage - simple building block with NO other agent resource dependencies"""
```

### **Processing Plugins (Execute During Pipeline Stages)**
Functional units that execute during specific pipeline stages to transform data, make decisions, or perform actions.

**PromptPlugin - Reasoning and Planning**
```python
class PromptPlugin(Plugin):
    """LLM-based reasoning and processing logic"""
    stage = THINK  # Default stage assignment
    dependencies = ["llm"]  # Can depend on any agent resources (Layer 3+)
    
    # Examples: ConversationHistory, ComplexPrompt, MemoryRetrieval
```

**ToolPlugin - External Function Calls**
```python
class ToolPlugin(Plugin):
    """External API calls and function execution"""
    stage = DO  # Default stage assignment
    
    async def execute_function(self, params: Dict[str, Any]) -> Any: ...
    
    # Examples: CalculatorTool, WeatherAPI, SearchTool
```

### **Interface Plugins (AdapterPlugin)**
Handle input/output transformation and protocol adaptation between external systems and the pipeline.

**InputAdapterPlugin - Media Ingestion**
```python
class InputAdapterPlugin(Plugin):
    """Convert external input into pipeline messages"""
    stage = INPUT  # Default stage assignment
    
    # Examples: HTTPAdapter, CLIAdapter, STTAdapter, WebSocketAdapter
```

**OutputAdapterPlugin - Response Delivery**
```python
class OutputAdapterPlugin(Plugin):
    """Convert pipeline responses to external formats"""
    stage = OUTPUT  # Default stage assignment
    
    # Examples: JSONFormatter, TTSAdapter, LoggingAdapter
```

### **Specialized Plugins**

**FailurePlugin - Error Handling**
```python
class FailurePlugin(Plugin):
    """Error recovery and user-friendly error responses"""
    stage = ERROR
    
    # Examples: BasicLogger, ErrorFormatter, FallbackErrorPlugin
```

## **4-Layer Resource Architecture**

### **Required Resources (Layer 3 - Canonical)**
The framework guarantees these three canonical resources are available to every pipeline execution:

```python
class StandardResources:
    llm: LLM           # Canonical LLM building block
    memory: Memory     # Canonical Memory building block  
    storage: Storage   # Canonical Storage building block
```

### **Custom Agent Resources (Layer 4 - User Compositions)**
Users create intelligent AgentResources by composing canonical ones:

```python
# User-defined: Memory with LLM-enhanced operations
class SmartMemory(AgentResource):
    def __init__(self, memory: Memory, llm: LLM, config: Dict | None = None):
        # Composes Layer 3 canonical resources
        self.memory = memory
        self.llm = llm
    
    async def contextual_recall(self, query: str) -> Dict[str, Any]:
        """Smart recall with LLM-enhanced semantic search"""
        # Complex behaviors that combine canonical resources

# User-defined: Complete RAG system
class RAGSystem(AgentResource):
    def __init__(self, memory: Memory, llm: LLM, storage: Storage, config: Dict | None = None):
        # Composes multiple canonical resources
```

### **Resource Composition Rules**
- **Layer 1 → Layer 2**: Infrastructure primitives composed into resource interfaces
- **Layer 2 → Layer 3**: Resource interfaces composed into canonical agent resources  
- **Layer 3 → Layer 4**: Canonical resources composed into custom intelligent resources
- **Plugins**: Can depend on any agent resources (Layer 3 or Layer 4)

### **Dependency Flow (Strict Hierarchy)**
```
Layer 1: Infrastructure Primitives (no dependencies)
    ↓
Layer 2: Resource Interfaces (depend only on Layer 1)
    ↓  
Layer 3: Canonical Agent Resources (depend only on Layer 2)
    ↓
Layer 4: Custom Agent Resources (depend only on Layer 3)
    ↓
Plugins (can depend on any agent resources)
```

## **Plugin Lifecycle Management**

### **Two-Phase Lifecycle**
```python
# Phase 1: Resource Initialization (Layers 1-4 in dependency order)
for layer in [infrastructure, resource_interfaces, canonical_resources, custom_resources]:
    for resource in dependency_order:
        await resource.initialize()
        container.register(resource)

# Phase 2: Pipeline Execution (Processing Plugins)
for stage in [INPUT, PARSE, THINK, DO, REVIEW, OUTPUT]:
    plugins = registry.get_plugins_for_stage(stage) 
    for plugin in plugins:
        await plugin.execute(context)
```

### **Lifecycle Characteristics**
- **Infrastructure/Resource Plugins**: Initialize once → persist → shutdown at end
- **Processing Plugins**: Execute per-request → stateless between executions
- **AdapterPlugins**: May run continuously (HTTP server) or per-request (CLI)

## **Plugin Development Patterns**

### **Stage Assignment Precedence**
1. **Config override**: `stage: DO` or `stages: [THINK, DO]` in configuration always wins
2. **Class default**: `stage = THINK` or `stages = [INPUT, OUTPUT]` in plugin class
3. **Safe fallback**: `THINK` stage if nothing else specified

### **Dependency Declaration with Constructor Injection**
```python
class ComplexPlugin(PromptPlugin):
    dependencies = ["smart_memory", "rag_system"]  # Can use Layer 3 or Layer 4 resources
    
    def __init__(self, config):
        super().__init__(config)
        # Dependencies injected by container via constructor
        self.smart_memory = None      # Set by container
        self.rag_system = None        # Set by container
```

### **Plugin Registration Order**
Plugins execute in YAML configuration order within each stage:
```yaml
plugins:
  prompts:
    step_1: {...}    # Runs first in THINK stage
    step_2: {...}    # Runs second in THINK stage  
    step_3: {...}    # Runs third in THINK stage
```

## **Configuration Integration**

```yaml
plugins:
  # Layer 1: Infrastructure Primitives
  infrastructure:
    postgres:
      type: entity.infrastructure.postgres:PostgresInfrastructure
      
  # Layer 2: Resource Interfaces (auto-wired to infrastructure)
  resources:
    database:
      type: entity.resources.database:DatabaseResource
      
  # Layer 3: Canonical Agent Resources
  agent_resources:
    memory:
      type: entity.agent.memory:Memory
      # Constructor: Memory(database=database, vector_store=vector_store)
      
  # Layer 4: Custom Agent Resources (user-defined)
  custom_resources:
    smart_memory:
      type: my_company.resources:SmartMemory
      # Constructor: SmartMemory(memory=memory, llm=llm)
      
  # Processing Plugins
  prompts:
    reasoning:
      type: my_company.plugins:ReasoningPlugin
      dependencies: ["smart_memory"]
```

## **Benefits of Unified Plugin + Resource Architecture**

1. **Single Learning Curve** - Developers master one Plugin interface for all extensions
2. **No Circular Dependencies** - Strict 4-layer hierarchy prevents cycles by design
3. **Progressive Complexity** - Start with canonical resources, compose custom as needed
4. **Consistent Tooling** - Same CLI commands, documentation patterns across all plugin types
5. **Clear Extension Points** - Obvious places to add functionality at each layer
6. **Framework Focus** - Core provides reliable building blocks, complexity lives in user code

## **Plugin Validation and Discovery**

The framework automatically validates plugin configurations to ensure:
- Required canonical resources are present (LLM, Memory, Storage)
- Resource dependency hierarchy is respected (no Layer violations)
- Stage assignments are compatible with plugin types
- Dependency chains are valid and acyclic
- Configuration parameters match plugin requirements

This unified taxonomy provides a clear mental model for developers while maintaining unlimited flexibility to extend the framework through the universal Plugin interface and composable resource architecture.


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





## 4. Plugin Stage Assignment: Explicit Declaration with Simple Defaults

**Decision**: Use explicit stage declaration with simple, predictable defaults that prioritize developer clarity over magic.

**Core Strategy**: Make stage assignment obvious and predictable - no surprises, no complex precedence hierarchies.

**New Stage Flow**:
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

**Simple Assignment Rules**:
1. **Config always wins**: `stage: DO` or `stages: [THINK, DO]` in configuration
2. **Class provides default**: `stage = DO` or `stages = [INPUT, OUTPUT]` in plugin class
3. **Fallback to THINK**: Safe default if nothing specified

**Implementation Pattern**:

**1. Single Stage Assignment (Most Common)**:
```python
# ToolPlugin auto-defaults to DO stage
class WeatherPlugin(ToolPlugin):
    stage = DO  # Simple, explicit default
    
# PromptPlugin auto-defaults to THINK stage  
class ReasoningPlugin(PromptPlugin):
    stage = THINK  # Clear default

# Override in config when needed
plugins:
  weather:
    type: WeatherPlugin
    stage: REVIEW  # Config override - now runs in REVIEW instead of DO
```

**2. Multi-Stage Assignment (When Needed)**:
```python
# InputAdapterPlugin handles input and output
class HTTPAdapter(InputAdapterPlugin):
    stages = [INPUT, OUTPUT]  # List for multiple stages
    
# Complex plugins can span multiple stages
class WorkflowPlugin(PromptPlugin):
    stages = [THINK, DO, REVIEW]  # Override default with multiple stages

# Config can override multi-stage too
plugins:
  http_adapter:
    type: HTTPAdapter  
    stages: [INPUT]  # Override to only handle input, not output
```

**3. Clear Stage Mental Model**:
- **INPUT**: "How do I receive and initial process the user's request?"
- **PARSE**: "How do I extract and structure the important information?"
- **THINK**: "What should I decide, plan, or reason about?"
- **DO**: "What actions or tools should I execute?"
- **REVIEW**: "Is my work good enough or does it need changes?"
- **OUTPUT**: "How should I format and deliver the final response?"

**4. Layer 0 Magic with Explicit Stages**:
```python
@agent.input     # → INPUT stage
@agent.parse     # → PARSE stage
@agent.prompt    # → THINK stage  
@agent.tool      # → DO stage
@agent.review    # → REVIEW stage
@agent.output    # → OUTPUT stage

# Generic with explicit stage
@agent.plugin(stage=DO)
def my_function():
    pass
```

**5. Progressive Complexity Path**:
1. **Level 1**: Decorators with automatic stage assignment (`@agent.tool` → DO)
2. **Level 2**: Class-based plugins with simple defaults (`stage = DO`)
3. **Level 3**: Multi-stage plugins with explicit lists (`stages = [THINK, DO]`)
4. **Level 4**: Config-driven stage overrides for environment-specific behavior

**Configuration Examples**:
```yaml
plugins:
  # Simple single stage
  weather_tool:
    type: WeatherPlugin  # Uses stage = DO from class
    
  # Override single stage  
  reasoning:
    type: ReasoningPlugin
    stage: REVIEW  # Override class default of THINK
    
  # Multi-stage plugin
  http_interface:
    type: HTTPAdapter
    stages: [INPUT, OUTPUT]  # Handle both input and output
    
  # Complex workflow
  data_processor:
    type: DataPlugin
    stages: [PARSE, THINK, DO]  # Multi-stage processing
```

**Simple Resolution Logic**:
```python
def get_plugin_stages(plugin_class, config):
    # 1. Config always wins (explicit override)
    config_stages = config.get('stages') or config.get('stage')
    if config_stages:
        return normalize_to_list(config_stages)
    
    # 2. Class default (explicit declaration)
    class_stages = getattr(plugin_class, 'stages', None) or getattr(plugin_class, 'stage', None)
    if class_stages:
        return normalize_to_list(class_stages)
    
    # 3. Safe fallback
    return [THINK]

def normalize_to_list(stages):
    """Convert single stage or list to consistent list format"""
    if isinstance(stages, str):
        return [PipelineStage.ensure(stages)]
    return [PipelineStage.ensure(s) for s in stages]
```

**Benefits**:
- **Predictable**: Same config always produces same stage assignment
- **Simple**: Two-level hierarchy (config → class → fallback)
- **Flexible**: Single stage for simple cases, list for complex cases
- **Debuggable**: Easy to trace why a plugin runs in specific stages
- **Intuitive**: Stage names match natural workflow progression

**No More Complex Precedence**: We eliminated the complex 5-level precedence hierarchy in favor of simple, predictable rules that developers can understand at a glance.

**Rationale**: Simplicity and predictability trump magic. Developers should never be surprised by when their plugin runs.




















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

For configuration examples see
[Tuning Circuit Breaker Thresholds](docs/source/error_handling.md#tuning-circuit-breaker-thresholds).

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


## 6. Scalability Architecture: Persistent State with Stateless Workers

**Decision**: Framework implements stateless worker processes with externally-persistent conversation state for horizontal scalability.

**Core Principle**: Worker processes hold no conversation state between requests, but the system maintains rich persistent state through external storage. Any worker instance can process any user conversation by loading state from external persistence.

**Implementation Pattern**:
```python
# Worker processes are stateless - no conversation data in instance variables
class PipelineWorker:
    def __init__(self, registries: SystemRegistries):
        self.registries = registries  # Shared resource pools only - no user data
    
    async def execute_pipeline(self, pipeline_id: str, message: str) -> Any:
        # Load conversation state from external storage each request
        memory = self.registries.resources.get("memory")
        conversation = await memory.load_conversation(pipeline_id)
        
        # Execute with ephemeral state (discarded after response)
        state = PipelineState(conversation=conversation, pipeline_id=pipeline_id)
        result = await self.run_stages(state)
        
        # Persist updated state back to external storage
        await memory.save_conversation(pipeline_id, state.conversation)
        return result
```
Implemented in `src/entity/worker/pipeline_worker.py`.

**Resource Implementation**:
```python
# Resources manage connection pooling and external persistence, not in-memory conversation state
class MemoryResource:
    def __init__(self, database: DatabaseResource):
        self.db_pool = database.get_connection_pool()  # Shared connection pool
    
    async def load_conversation(self, pipeline_id: str) -> List[ConversationEntry]:
        # Load conversation history from external database each request
        async with self.db_pool.acquire() as conn:
            return await conn.fetch_conversation(pipeline_id)
    
    async def save_conversation(self, pipeline_id: str, conversation: List[ConversationEntry]):
        # Persist conversation updates to external database
        async with self.db_pool.acquire() as conn:
            await conn.store_conversation(pipeline_id, conversation)
```

**Key Requirements**:
- Worker processes hold no conversation state between requests
- All user/conversation context loaded fresh from external storage per execution
- `PipelineState` created and discarded for each pipeline execution
- External persistence (MemoryResource) manages conversation continuity
- Any worker instance can process any user conversation through state loading
- Resources provide connection pooling and external persistence, not in-memory data storage

**Benefits**: 
- **Horizontal scaling**: Add worker processes without state coordination
- **Process resilience**: Workers can be restarted/killed without data loss
- **Load balancing**: Any worker can handle any user request
- **Conversation continuity**: Rich conversation history through external persistence
- **Standard deployment patterns**: Stateless worker pools with shared database

**Related Decisions**: See [Memory Resource Consolidation](#10-memory-resource-consolidation) for how conversation state is structured, and [Multi-User Support](#29-multi-user-support-user_id-parameter-pattern) for user isolation patterns within this architecture.



## 7. Response Termination Control

**Decision**: Only OUTPUT stage plugins can set the final pipeline response that terminates the iteration loop.

**Rationale**:
- Creates clear separation of concerns across pipeline stages
- INPUT handles incoming requests and initial processing
- PARSE extracts and structures important information
- THINK performs reasoning and planning
- DO executes tools and actions
- REVIEW validates and formats intermediate results
- OUTPUT handles final response composition and delivery
- Prevents early termination from skipping important downstream processing
- Makes pipeline flow predictable and debuggable

**Implementation**:
- `context.say()` method restricted to OUTPUT stage plugins only (sets final response)
- Pipeline continues looping (INPUT → PARSE → THINK → DO → REVIEW → OUTPUT) until an OUTPUT plugin calls `say()`
- Earlier stages use `context.think()` to store intermediate thoughts for OUTPUT plugins to access via `context.reflect()`
- Maximum iteration limit (default 5) prevents infinite loops when no OUTPUT plugin sets a response

**Usage Pattern**:
```python
# THINK stage - store analysis for later use
class ReasoningPlugin(PromptPlugin):
    stage = THINK
    
    async def _execute_impl(self, context: PluginContext) -> None:
        analysis = await self.call_llm(context, "Analyze this request...")
        await context.think("reasoning_result", analysis.content)
        # No context.say() - plugin cannot terminate pipeline

# DO stage - execute actions and store results
class ActionPlugin(ToolPlugin):
    stage = DO
    
    async def _execute_impl(self, context: PluginContext) -> None:
        reasoning = await context.reflect("reasoning_result", "")
        result = await context.tool_use("search", query=reasoning)
        await context.think("action_result", result)
        # No context.say() - plugin cannot terminate pipeline

# OUTPUT stage - compose final response
class ResponsePlugin(PromptPlugin):
    stage = OUTPUT
    
    async def _execute_impl(self, context: PluginContext) -> None:
        reasoning = await context.reflect("reasoning_result", "")
        action_result = await context.reflect("action_result", "")
        
        final_response = await self.call_llm(
            context,
            f"Based on analysis: {reasoning} and results: {action_result}, provide final response"
        )
        
        await context.say(final_response.content)  # This terminates the pipeline
```

**Configuration Example**:
```yaml
plugins:
  reasoning:
    type: ReasoningPlugin
    stage: THINK
    
  search_action:
    type: ActionPlugin  
    stage: DO
    
  response_formatter:
    type: ResponsePlugin
    stage: OUTPUT  # Only OUTPUT plugins can call context.say()
```

**Pipeline Flow**:
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
  ↓       ↓       ↓     ↓      ↓        ↓
 process extract reason act   validate  say() ← TERMINATES
```

**Error Handling**:
- If `context.say()` is called from non-OUTPUT stage: Immediate error with clear message
- If no OUTPUT plugin calls `say()` after max iterations: Pipeline fails with timeout error
- If multiple OUTPUT plugins call `say()`: First call wins, subsequent calls are warnings

**Benefits**: 
- **Clear responsibility**: Only OUTPUT stage handles final responses
- **Predictable flow**: Pipeline always completes full cycle before terminating
- **Debugging clarity**: Easy to find where responses are generated
- **Consistent processing**: All validation and formatting happens before output
- **Natural separation**: INPUT gets data in, OUTPUT sends data out




## 8. Stage Results Accumulation Pattern

**Decision**: Use stage results accumulation with anthropomorphic cognitive methods (`context.think()`, `context.reflect()`) for inter-stage communication within pipeline execution.

**Rationale**:
- Builds on unified state management with intuitive anthropomorphic naming
- Maintains pipeline mental model where each stage produces discrete cognitive outputs
- Temporary thoughts persist across pipeline iterations, enabling context accumulation
- Provides explicit traceability for debugging and observability
- Allows flexible composition patterns in OUTPUT plugins
- Natural metaphor: agents "think" during processing and "reflect" on previous thoughts

**Implementation**:
- Earlier stages use `await context.think(key, value)` to save intermediate thoughts
- OUTPUT plugins use `await context.reflect(key)` to access stored thoughts for response composition
- `await context.reflect(key, default)` enables conditional logic based on available thoughts
- Temporary thoughts are cleared between separate pipeline executions but persist across iterations within the same execution
- Distinguished from persistent memory (`context.remember()`/`context.recall()`) which survives across sessions

**Stage Flow with Thought Accumulation**:
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
  ↓       ↓       ↓     ↓      ↓        ↓
think() think() think() think() think() reflect() + say()
```

**Usage Examples**:
```python
# INPUT stage - capture and process initial request
class HTTPInputPlugin(InputAdapterPlugin):
    stage = INPUT
    
    async def _execute_impl(self, context: PluginContext) -> None:
        request_data = await self.parse_http_request(context)
        await context.think("raw_request", request_data)
        await context.think("user_intent", self._extract_intent(request_data))

# PARSE stage - extract structured information
class DataParserPlugin(PromptPlugin):
    stage = PARSE
    
    async def _execute_impl(self, context: PluginContext) -> None:
        raw_request = await context.reflect("raw_request", {})
        parsed_data = await self.call_llm(context, f"Extract key information from: {raw_request}")
        await context.think("parsed_entities", parsed_data.content)

# THINK stage - analyze and store thoughts
class AnalysisPlugin(PromptPlugin):
    stage = THINK
    
    async def _execute_impl(self, context: PluginContext) -> None:
        user_intent = await context.reflect("user_intent", "")
        entities = await context.reflect("parsed_entities", "")
        
        analysis = await self.call_llm(context, f"Analyze intent: {user_intent} with entities: {entities}")
        await context.think("analysis_result", analysis.content)
        await context.think("complexity_score", self._calculate_complexity(user_intent))

# DO stage - use previous thoughts for actions
class ActionPlugin(ToolPlugin):
    stage = DO
    
    async def _execute_impl(self, context: PluginContext) -> None:
        analysis = await context.reflect("analysis_result", "")
        complexity = await context.reflect("complexity_score", 1)
        
        if complexity > 5:
            result = await context.tool_use("advanced_search", query=analysis)
        else:
            result = await context.tool_use("simple_search", query=analysis)
        
        await context.think("action_results", result)

# REVIEW stage - validate and enhance results
class ReviewPlugin(PromptPlugin):
    stage = REVIEW
    
    async def _execute_impl(self, context: PluginContext) -> None:
        action_results = await context.reflect("action_results", {})
        analysis = await context.reflect("analysis_result", "")
        
        validation = await self.call_llm(
            context, 
            f"Review if results {action_results} properly address the analysis {analysis}"
        )
        
        await context.think("validation_result", validation.content)
        await context.think("confidence_score", self._extract_confidence(validation.content))

# OUTPUT stage - compose final response using all thoughts
class ResponsePlugin(PromptPlugin):
    stage = OUTPUT
    
    async def _execute_impl(self, context: PluginContext) -> None:
        # Gather all accumulated thoughts
        analysis = await context.reflect("analysis_result", "")
        action_results = await context.reflect("action_results", {})
        validation = await context.reflect("validation_result", "")
        confidence = await context.reflect("confidence_score", 0.5)
        
        # Compose final response
        response = await self.call_llm(
            context, 
            f"Create final response based on:\n"
            f"Analysis: {analysis}\n"
            f"Results: {action_results}\n"
            f"Validation: {validation}\n"
            f"Confidence: {confidence}"
        )
        
        await context.say(response.content)  # Terminate pipeline
```

**Configuration Example**:
```yaml
plugins:
  http_input:
    type: HTTPInputPlugin
    stage: INPUT
    
  data_parser:
    type: DataParserPlugin  
    stage: PARSE
    
  analyzer:
    type: AnalysisPlugin
    stage: THINK
    
  search_tool:
    type: ActionPlugin
    stage: DO
    
  reviewer:
    type: ReviewPlugin
    stage: REVIEW
    
  response_formatter:
    type: ResponsePlugin
    stage: OUTPUT
```

**Thought Lifecycle**:
```python
# Thoughts persist within single pipeline execution
Pipeline Execution 1:
  INPUT:  think("user_intent", "weather query")
  PARSE:  reflect("user_intent") → "weather query"
          think("location", "San Francisco") 
  THINK:  reflect("location") → "San Francisco"
          think("analysis", "need current weather")
  DO:     reflect("analysis") → "need current weather"
          think("weather_data", {...})
  OUTPUT: reflect("weather_data") → {...}
          say("It's 72°F in San Francisco")

# Thoughts cleared between executions
Pipeline Execution 2:
  INPUT:  reflect("user_intent") → None (cleared from previous execution)
```

**Benefits**:
- **Intuitive naming**: `think()` and `reflect()` match natural cognitive processes
- **Clear data flow**: Explicit thought storage and retrieval for debugging visibility
- **Flexible response composition**: OUTPUT plugins can access any previous thoughts
- **Natural support for iterative pipeline execution**: Thoughts accumulate across iterations
- **Separation of concerns**: Temporary thoughts vs persistent memory clearly distinguished
- **Complete pipeline visibility**: Each stage's contributions are traceable
- **Conditional logic**: Plugins can adapt behavior based on previous stage results





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

**Decision**: Consolidate all memory-related components into a single unified `Memory` resource that provides external persistence for the stateless worker architecture and serves as the backend for both simple and advanced memory operations.

**Rationale**:
- Eliminates architectural ambiguity between separate memory components
- Single responsibility for all external persistence concerns (key-value, conversations, search)
- Simplifies resource dependencies - plugins only need "memory" resource
- Cleaner configuration with one memory section instead of multiple
- Natural API progression from simple anthropomorphic methods to advanced technical operations
- **Supports stateless workers**: Provides the external persistence layer that enables any worker to load/save conversation state
- **Dual interface backend**: Powers both PluginContext anthropomorphic methods and direct technical access

**Implementation**:
- `Memory` class provides advanced technical interface for complex operations
- Serves as backend for PluginContext anthropomorphic methods (`remember()`, `recall()`, `think()`, `say()`)
- Core conversation methods `save_conversation()` and `load_conversation()` handle external conversation persistence
- Requires a database backend for persistence; optionally uses a vector_store for similarity search
- Replaces SimpleMemoryResource, MemoryResource, ConversationManager, and Memory interface
- **External persistence guarantee**: All data persisted to database/storage, never held in Memory resource instance variables

**External Persistence Architecture with Post-Construction Dependency Injection**:
```python
class Memory(ResourcePlugin):
    dependencies = ["database", "vector_store?"]
    
    def __init__(self, config: Dict | None = None):
        super().__init__(config or {})
        # Dependencies injected by container after construction
        self.database = None      # Set by container
        self.vector_store = None  # Set by container
        # No instance variables for conversation data
    
    async def initialize(self) -> None:
        """Called after dependency injection is complete"""
        # Validation that required dependencies were injected
        if self.database is None:
            raise ResourceInitializationError("Database dependency not injected")
    
    # Advanced technical interface for complex operations
    async def query(self, sql: str, params: list = None) -> List[Dict]:
        """Execute SQL queries for complex data operations"""
        return await self.database.execute_query(sql, params)
    
    async def vector_search(self, query: str, k: int = 5) -> List[Dict]:
        """Perform semantic similarity search"""
        return await self.vector_store.similarity_search(query, k)
    
    async def batch_store(self, key_value_pairs: Dict[str, Any]) -> None:
        """Bulk storage operations for efficiency"""
        await self.database.batch_insert(key_value_pairs)
    
    # Backend methods for PluginContext anthropomorphic interface
    async def store_persistent(self, key: str, value: Any) -> None:
        """Backend for context.remember() - persist to external database"""
        await self.database.store_key_value(key, value)
    
    async def fetch_persistent(self, key: str, default: Any = None) -> Any:
        """Backend for context.recall() - load from external database"""
        return await self.database.fetch_key_value(key, default)
    
    async def delete_persistent(self, key: str) -> None:
        """Backend for context.forget() - remove from external database"""
        await self.database.delete_key_value(key)
    
    # Conversation management (external persistence)
    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        """Always load from external database"""
        return await self.database.fetch_conversation(conversation_id)
    
    async def save_conversation(self, conversation_id: str, conversation: List[ConversationEntry]):
        """Always persist to external database"""
        await self.database.store_conversation(conversation_id, conversation)
    
    async def add_conversation_entry(self, conversation_id: str, entry: ConversationEntry):
        """Backend for context.say() - append to external conversation"""
        current = await self.load_conversation(conversation_id)
        current.append(entry)
        await self.save_conversation(conversation_id, current)
    
    # Advanced conversation analytics
    async def conversation_search(self, query: str, user_id: str = None, days: int = None) -> List[Dict]:
        """Search across conversation history with semantic matching"""
        return await self.vector_store.search_conversations(query, user_id, days)
    
    async def conversation_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get conversation analytics for a user"""
        return await self.database.conversation_stats(user_id)
```

**Container Injection Pattern**:
```python
# Container handles dependency injection after construction
class ResourceContainer:
    async def build_all(self):
        # 1. Instantiate all resources with config only
        memory = Memory(config)
        database = DatabaseResource(config)
        vector_store = VectorStoreResource(config)
        
        # 2. Inject dependencies as attributes (post-construction)
        memory.database = database
        memory.vector_store = vector_store
        
        # 3. Initialize in dependency order
        await database.initialize()
        await vector_store.initialize()
        await memory.initialize()  # Validates dependencies were injected
```

**Configuration Example**:
```yaml
plugins:
  infrastructure:
    postgres:
      type: entity.infrastructure.postgres:PostgresInfrastructure

  resources:
    database:
      type: entity.resources.database:PostgresResource
      host: localhost
      port: 5432

    vector_store:
      type: entity.resources.vector:PgVectorStore
      dimensions: 768

  agent_resources:
    memory:
      type: entity.resources.memory:Memory
      # Dependencies automatically injected by container
      # No need to specify database/vector_store config here
```

**Usage Patterns**:
```python
# Simple anthropomorphic access (most common)
await context.remember("user_style", "formal")
user_style = await context.recall("user_style")
await context.say("Here's my response")

# Advanced technical access (complex operations)
memory = context.get_resource("memory")
results = await memory.query("SELECT * FROM user_prefs WHERE category = ?", ["style"])
similar_conversations = await memory.conversation_search("customer complaints", days=30)
stats = await memory.conversation_statistics(context.user_id)
```

**Key Benefits of Consistent Dependency Injection**:
1. **Circular dependency safe**: Topological sorting handles complex dependency graphs
2. **Container-friendly**: Standardized injection pattern across all resources
3. **Test-friendly**: Easy to mock dependencies by setting attributes
4. **Validation-ready**: `initialize()` method can validate all dependencies are present
5. **Hot-reload compatible**: Dependencies can be re-injected during configuration updates

**Related Decisions**: This decision provides the external persistence layer that supports [Persistent State with Stateless Workers](#6-scalability-architecture-persistent-state-with-stateless-workers) architecture and serves as the unified backend for [State Management Consolidation](#23-state-management-consolidation-dual-interface-pattern), using the consistent dependency injection pattern from [Resource Dependency Injection Pattern](#11-resource-dependency-injection-pattern).






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
        
        # Simple anthropomorphic approach for user preferences:
        user_style = await context.recall("communication_style", "professional")
        await context.think("user_style", user_style)
        
        # Or advanced technical approach for complex queries:
        prefs = await memory.query("SELECT style FROM user_prefs WHERE user_id=?", [context.user_id])
        similar = await memory.vector_search(context.message, k=3)
        await context.think("user_style", prefs[0]["style"])
        await context.think("relevant_context", similar)
        
        # Generate personalized response
        response = await self.call_llm(
            context, 
            f"Respond in {await context.reflect('user_style')} style to: {context.message}"
        )
        
        # Update user preferences and respond
        await context.remember("last_topic", self._extract_topic(context.message))
        await context.say(response.content)
```

**Rationale**: Maintains framework focus on providing powerful primitives rather than opinionated solutions. Enables unlimited memory patterns while keeping core simple. The anthropomorphic API (`remember()`, `recall()`, `think()`, `reflect()`) provides intuitive access for common cases, while direct memory resource access enables complex operations.



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

## 23. State Management Consolidation: Dual Interface Pattern

**Decision**: Implement a dual interface system with anthropomorphic PluginContext methods for simple use cases and advanced Memory resource access for complex operations.

### Rationale

**Eliminated Complexity** from multi-layered state management:
- Four overlapping storage mechanisms consolidated into two clear interfaces
- Unclear boundaries between temporary vs persistent data resolved
- Data duplication eliminated through unified backend storage
- Reduced cognitive overhead through anthropomorphic method naming

### Dual Interface Pattern

**Simple Interface (PluginContext) - Anthropomorphic Methods:**
```python
# Human-like memory operations (persistent data)
await context.remember("user_prefs", data)     # Store persistent data
await context.recall("user_prefs")             # Retrieve persistent data  
await context.forget("user_prefs")             # Delete persistent data

# Cognitive operations (temporary data - dies with pipeline run)
await context.think("analysis", result)        # Store temporary thoughts
await context.reflect("analysis")              # Retrieve temporary thoughts
await context.clear_thoughts()                 # Clear all temporary data

# Communication operations (conversation history)
await context.say("Here's my response")        # Add to conversation
await context.conversation()                   # Get conversation history
await context.listen()                         # Get last user message
```

**Advanced Interface (Memory Resource) - Technical Operations:**
```python
# Direct memory resource access for complex operations
memory = context.get_resource("memory")

# Advanced persistent storage operations
await memory.query("SELECT * FROM user_prefs WHERE...")  # SQL queries
await memory.vector_search("similar content", k=5)       # Vector operations
await memory.batch_store(key_value_pairs)                # Bulk operations
await memory.conversation_search("topic", days=30)       # Conversation analysis

# Low-level conversation management
await memory.load_conversation(conversation_id)
await memory.save_conversation(conversation_id, history)
await memory.conversation_statistics(user_id)
```

### Key Principles

1. **Progressive Disclosure**: Simple anthropomorphic methods for common cases, advanced resource for complex operations
2. **Unified Backend**: Both interfaces operate on the same external storage
3. **All Async**: Every operation that touches external storage is async
4. **Anthropomorphic Simplicity**: Natural language methods reduce cognitive load
5. **Technical Power**: Advanced interface provides full database/vector capabilities
6. **Single Source of Truth**: All data flows through unified Memory resource backend

### Implementation Architecture

```python
class PluginContext:
    def __init__(self, state: PipelineState, registries: Any, user_id: str):
        self._memory = registries.resources.get("memory")
        self._user_id = user_id
        self._temporary_thoughts = {}  # Cleared after pipeline execution
    
    # Anthropomorphic persistent memory operations
    async def remember(self, key: str, value: Any) -> None:
        """Store user-specific persistent data"""
        namespaced_key = f"{self._user_id}:{key}"
        await self._memory.store_persistent(namespaced_key, value)
    
    async def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve user-specific persistent data"""
        namespaced_key = f"{self._user_id}:{key}"
        return await self._memory.fetch_persistent(namespaced_key, default)
    
    async def forget(self, key: str) -> None:
        """Delete user-specific persistent data"""
        namespaced_key = f"{self._user_id}:{key}"
        await self._memory.delete_persistent(namespaced_key)
    
    # Cognitive temporary operations
    async def think(self, key: str, value: Any) -> None:
        """Store temporary thought (pipeline execution only)"""
        self._temporary_thoughts[key] = value
    
    async def reflect(self, key: str, default: Any = None) -> Any:
        """Retrieve temporary thought"""
        return self._temporary_thoughts.get(key, default)
    
    async def clear_thoughts(self) -> None:
        """Clear all temporary thoughts"""
        self._temporary_thoughts.clear()
    
    # Conversation operations
    async def say(self, message: str) -> None:
        """Add agent response to conversation"""
        await self._memory.add_conversation_entry(
            self._conversation_id, 
            ConversationEntry(content=message, role="assistant")
        )
    
    async def conversation(self) -> List[ConversationEntry]:
        """Get full conversation history"""
        return await self._memory.load_conversation(self._conversation_id)
    
    async def listen(self) -> str | None:
        """Get the last user message"""
        history = await self.conversation()
        user_messages = [entry for entry in history if entry.role == "user"]
        return user_messages[-1].content if user_messages else None

# Advanced Memory Resource remains technical
class Memory(ResourcePlugin):
    async def store_persistent(self, key: str, value: Any) -> None:
        await self.database.store_key_value(key, value)
    
    async def fetch_persistent(self, key: str, default: Any = None) -> Any:
        return await self.database.fetch_key_value(key, default)
    
    async def query(self, sql: str, params: list = None) -> List[Dict]:
        return await self.database.execute_query(sql, params)
    
    async def vector_search(self, query: str, k: int = 5) -> List[Dict]:
        return await self.vector_store.similarity_search(query, k)
```

This dual interface provides **anthropomorphic simplicity** for 80% of use cases while maintaining **technical power** for complex scenarios, all built on the same unified external storage backend.

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
    Stage.INPUT: ["http_input", "validate_request"],
    Stage.PARSE: ["extract_info", "validate_account"],
    Stage.THINK: ["classify_issue", "route_specialist"],
    Stage.DO: ["resolution_tools", "gather_data"],
    Stage.REVIEW: ["validate_solution", "check_policy"],
    Stage.OUTPUT: ["format_response", "send_notification"]
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
pipeline = Pipeline(workflow=workflow)

# Combine them
agent = Agent(pipeline=pipeline)
```

**Complete Workflow Examples:**

**Basic Support Workflow:**
```python
SupportWorkflow = {
    Stage.INPUT: ["web_interface", "email_intake"],
    Stage.PARSE: ["extract_customer_info", "categorize_request"],
    Stage.THINK: ["analyze_issue", "check_knowledge_base"],
    Stage.DO: ["search_solutions", "escalate_if_needed"],
    Stage.REVIEW: ["validate_response", "ensure_completeness"],
    Stage.OUTPUT: ["format_reply", "update_ticket", "send_response"]
}
```

**Data Analysis Workflow:**
```python
AnalysisWorkflow = {
    Stage.INPUT: ["file_upload", "api_data_fetch"],
    Stage.PARSE: ["clean_data", "validate_schema"],
    Stage.THINK: ["identify_patterns", "select_analysis_method"],
    Stage.DO: ["run_analysis", "generate_charts"],
    Stage.REVIEW: ["verify_results", "check_statistical_significance"],
    Stage.OUTPUT: ["create_report", "export_visualizations"]
}
```

**Multi-Environment Workflow:**
```python
class ProductionWorkflow:
    """Full 6-stage workflow for production environments"""
    stages = {
        Stage.INPUT: ["secure_input", "rate_limiting"],
        Stage.PARSE: ["validate_input", "extract_entities"],
        Stage.THINK: ["complex_reasoning", "multi_step_planning"],
        Stage.DO: ["execute_actions", "external_api_calls"],
        Stage.REVIEW: ["quality_check", "compliance_validation"],
        Stage.OUTPUT: ["format_output", "audit_logging", "response_delivery"]
    }

class DevelopmentWorkflow:
    """Simplified workflow for development/testing"""
    stages = {
        Stage.INPUT: ["simple_input"],
        Stage.THINK: ["basic_reasoning"],
        Stage.DO: ["mock_actions"],
        Stage.OUTPUT: ["debug_output"]
    }
```

**Progressive Complexity Examples:**

**Level 1: Simple Stage Mapping**
```python
# Just map stages to plugin lists
SimpleWorkflow = {
    Stage.THINK: ["reasoning_plugin"],
    Stage.DO: ["action_plugin"],
    Stage.OUTPUT: ["response_plugin"]
}
```

**Level 2: Conditional Logic (Future)**
```python
# Future: workflows with conditional execution
class ConditionalWorkflow:
    def get_stages(self, context):
        if context.user_type == "premium":
            return {
                Stage.THINK: ["advanced_reasoning"],
                Stage.DO: ["premium_tools"],
                Stage.OUTPUT: ["detailed_response"]
            }
        else:
            return {
                Stage.THINK: ["basic_reasoning"],
                Stage.OUTPUT: ["simple_response"]
            }
```

**Key Design Principles:**
1. **Workflows are stateless blueprints** - they define behavior, not execution state
2. **Pipelines handle execution** - they manage resources, state, and plugin orchestration
3. **Clean separation of concerns** - workflow logic separate from infrastructure concerns
4. **Backward compatible** - existing stage-based configurations continue to work
5. **Progressive complexity** - simple stage mappings initially, conditional logic later
6. **Complete stage coverage** - workflows can utilize all 6 stages (INPUT → PARSE → THINK → DO → REVIEW → OUTPUT)

**Configuration Integration:**
```yaml
# Workflow can be defined in YAML and referenced
workflows:
  customer_support:
    input: ["web_interface"]
    parse: ["extract_customer_info"]
    think: ["analyze_issue"]
    do: ["search_solutions"]
    review: ["validate_response"]
    output: ["format_reply"]

agents:
  support_bot:
    workflow: customer_support
    resources:
      llm: openai
      memory: postgres
```

This architecture maintains your existing stateless execution model while providing the higher-level abstractions developers need for complex agent behaviors across all 6 pipeline stages.













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

**Complete Stage Decorator Set:**

**Full 6-Stage Coverage**
```python
@agent.input     # → INPUT stage
def http_handler(request_data: dict) -> dict:
    return {"user_message": request_data.get("message", "")}

@agent.parse     # → PARSE stage  
def extract_entities(message: str) -> dict:
    return {"entities": extract_important_info(message)}

@agent.prompt    # → THINK stage
def reasoning(message: str) -> str:
    return f"Analyze this request: {message}"  # LLM automatically called

@agent.tool      # → DO stage
def weather_check(location: str) -> dict:
    return get_weather_data(location)

@agent.review    # → REVIEW stage
def validate_response(response: str) -> str:
    return f"Check if this response is appropriate: {response}"

@agent.output    # → OUTPUT stage
def format_json(content: str) -> dict:
    return {"response": content, "timestamp": datetime.now()}

# Generic decorator with explicit stage
@agent.plugin(stage=THINK)
def custom_reasoning():
    pass

@agent.plugin(stages=[PARSE, REVIEW])  # Multi-stage
def data_validator():
    pass
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
- `@agent.input` functions auto-register to INPUT stage
- `@agent.parse` functions auto-register to PARSE stage
- `@agent.prompt` functions auto-register to THINK stage with LLM integration
- `@agent.tool` functions auto-register to DO stage
- `@agent.review` functions auto-register to REVIEW stage with LLM integration
- `@agent.output` functions auto-register to OUTPUT stage
- Functions automatically added to global agent instance
- No explicit plugin class creation required

**2. Auto-LLM Integration**
- Functions decorated with `@agent.prompt` and `@agent.review` automatically call LLM
- Return strings treated as prompts sent to Ollama
- LLM response becomes function's actual return value
- Eliminates manual `await context.call_llm()` boilerplate

**3. Implicit Resource Access**
```python
@agent.prompt
def contextual_chat(message: str, context) -> str:
    # Context parameter triggers auto-injection
    history = await context.recall("chat_history", [])
    await context.remember("last_interaction", message)
    return f"Given conversation history {history}, respond to: {message}"

@agent.input
def smart_input(request: dict, context) -> dict:
    # INPUT stage can access context for preprocessing
    user_prefs = await context.recall("user_preferences", {})
    return {"message": request["text"], "preferences": user_prefs}
```

**Complete Pipeline Example:**
```python
from entity import agent

@agent.input
def web_input(request: dict) -> str:
    return request.get("message", "")

@agent.parse
def extract_intent(message: str) -> dict:
    return {"intent": classify_intent(message), "entities": extract_entities(message)}

@agent.prompt
def plan_response(message: str, context) -> str:
    parsed = await context.reflect("extracted_data", {})
    return f"Plan response for intent: {parsed.get('intent')} with message: {message}"

@agent.tool
def search_knowledge(query: str) -> dict:
    return {"results": search_database(query)}

@agent.review  
def check_quality(response: str) -> str:
    return f"Review this response for accuracy and helpfulness: {response}"

@agent.output
def format_response(content: str) -> dict:
    return {"response": content, "status": "success"}

# Agent automatically handles full pipeline
response = agent.chat("What's the weather like?")
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
    await context.remember("topic", extract_topic(message))
    return f"Respond to: {message}"

# Layer 3: Full plugin classes
class AdvancedChatPlugin(PromptPlugin):
    stage = THINK
    dependencies = ["llm", "memory", "vector_store"]
```

**Key Design Principles:**
1. **Local-first architecture** - works offline, no external services required
2. **Real AI immediately** - actual LLM responses, not mock/echo behavior
3. **Zero configuration burden** - sensible defaults for everything
4. **Decorator-based simplicity** - familiar Python patterns, minimal learning curve
5. **Auto-magic with escape hatches** - magic behavior with clear upgrade paths
6. **Resource abstraction** - hide complexity while maintaining full power
7. **Complete pipeline coverage** - decorators for all 6 stages

**Benefits:**
- **Privacy by default**: Data never leaves user's machine during development
- **Cost-free experimentation**: No API billing concerns for learning/testing
- **Offline development**: Works without internet connectivity
- **Educational value**: Users learn local AI deployment patterns
- **Production graduation**: Easy scaling to cloud resources when needed
- **Full pipeline control**: Can build complete agents with just decorators

This Layer 0 positions the framework as the **"local-first AI agent framework"** while maintaining full architectural compatibility with enterprise-scale deployments through existing progressive disclosure layers.




















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

**Decision**: Implement multi-user support through a simple `user_id` parameter in pipeline execution, using conversation namespacing for user isolation within the stateless worker architecture.

**Core Purpose:**
- **User isolation**: Separate conversation state per user within same agent instance
- **Resource efficiency**: Share agent logic and resources across users
- **Simplicity**: Minimal architectural complexity with maximum functionality
- **Clear security model**: Different user bases use separate deployments
- **Stateless worker compatibility**: User isolation through external persistence namespacing

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

**Memory Resource Integration with External Persistence**
```python
class Memory(ResourcePlugin):
    async def save_conversation(self, conversation_id: str, history: List[ConversationEntry]) -> None:
        # conversation_id format: "{user_id}_{pipeline_id}"
        # Persist to external database, not instance variables
        await self.database.store_conversation(conversation_id, history)

    async def load_conversation(self, conversation_id: str) -> List[ConversationEntry]:
        # Load from external database each request
        # Automatic user isolation through namespaced conversation_id
        return await self.database.fetch_conversation(conversation_id)
        
    async def remember(self, key: str, value: Any) -> None:
        """Store user-specific persistent data with automatic namespacing"""
        # Persist to external storage with user namespace
        await self.database.store_key_value(key, value)

    async def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve user-specific value from external persistent storage"""
        return await self.database.fetch_key_value(key, default)
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
        
        # Create user-specific pipeline_id for external persistence
        pipeline_id = f"{user_id}_{generate_pipeline_id()}"
        
        # Load user's conversation history from external storage
        memory = self._runtime.capabilities.resources.get("memory")
        conversation_history = await memory.load_conversation(pipeline_id)
        
        # Create ephemeral pipeline state (discarded after execution)
        state = PipelineState(
            conversation=conversation_history + [ConversationEntry(
                content=message, 
                role="user", 
                timestamp=datetime.now()
            )],
            pipeline_id=pipeline_id,
            metrics=MetricsCollector(),
        )
        
        # Execute pipeline with stateless worker
        result = await execute_pipeline(
            message, 
            self._runtime.capabilities,
            user_id=user_id,
            state=state
        )
        
        # Persist updated conversation to external storage
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

    async def remember(self, key: str, value: Any) -> None:
        """Persist user-specific value in external storage via memory resource"""
        if self._memory is not None:
            # Automatically namespace key with user_id for external persistence
            namespaced_key = f"{self._user_id}:{key}"
            await self._memory.remember(namespaced_key, value)

    async def memory(self, key: str, default: Any | None = None) -> Any:
        """Retrieve user-specific value from external persistent storage"""
        if self._memory is None:
            return default
        namespaced_key = f"{self._user_id}:{key}"
        return await self._memory.get(namespaced_key, default)
```

**User Isolation Strategy:**
- **Conversation namespacing**: `pipeline_id = f"{user_id}_{generate_pipeline_id()}"`
- **Memory isolation**: Memory keys automatically prefixed with `user_id:` in external storage
- **Shared resources**: LLM, tools, and plugin logic shared across users
- **No cross-user data leakage**: User isolation enforced at external persistence layer
- **External persistence**: All user data stored in database/external storage, never in worker memory

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
2. **Natural isolation**: user_id becomes conversation and memory namespace in external storage
3. **Resource sharing**: Efficient use of LLM and infrastructure resources
4. **Clear boundaries**: Different user bases require separate deployments
5. **Zero overhead**: No runtime performance impact for user isolation
6. **Backward compatibility**: Existing single-user agents continue working
7. **External persistence**: All user state stored externally, supporting stateless worker architecture

**Benefits:**
- **Cost efficiency**: Multiple users share same agent infrastructure
- **Simple scaling**: Add more users until resource limits, then scale instances
- **Security by design**: User data automatically isolated through external storage namespacing
- **Operational simplicity**: No complex multi-tenant management required
- **Clear upgrade path**: Easy to move users to dedicated instances if needed
- **Horizontal scalability**: Any worker can handle any user through external state loading

**Related Decisions**: This decision builds on [Persistent State with Stateless Workers](#6-scalability-architecture-persistent-state-with-stateless-workers) and [Memory Resource Consolidation](#10-memory-resource-consolidation) to provide user isolation through external persistence namespacing.

This pattern provides robust multi-user support with essentially zero architectural overhead while maintaining clear security boundaries, operational simplicity, and full compatibility with the stateless worker scaling architecture.

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


## Reads

### Benchmarking Tools
- https://github.com/THUDM/AgentBench
- https://github.com/web-arena-x/webarena
- https://huggingface.co/spaces/gaia-benchmark/leaderboard
- https://github.com/xingyaoww/mint-bench
- https://github.com/facebookresearch/sweet_rl
- https://github.com/ryoungj/ToolEmu
- https://github.com/HowieHwong/MetaTool