# Architecture Decisions Summary

The following architecture decisions were made through systematic analysis of the Entity Pipeline Framework to optimize for developer adoption, scalability, and maintainability.

## 1. Core Mental Model: Adaptive Pipeline-to-State Machine

**Decision**: Implement progressive complexity from simple pipeline to sophisticated state machine behaviors.

**Rationale**: 
- Start with pipeline mental model for immediate adoption (80% of use cases)
- Provide clear upgrade paths to state machine complexity as needs grow
- Maintains pipeline simplicity while enabling sophisticated behaviors
- Aligns with "Progressive Disclosure" principle and FastAPI's success pattern

**Implementation**: 
- Default linear flow: PARSE → THINK → DO → REVIEW → DELIVER
- Optional looping when no response generated (current hybrid approach)
- Advanced users can access full state machine capabilities

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
- Earlier stages use `context.set_stage_result()` to store intermediate outputs for DELIVER plugins to access
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

