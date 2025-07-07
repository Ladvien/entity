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
