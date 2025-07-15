# Entity Pipeline Contributor Guide

This repository contains a plugin-based framework for building AI agents.
Use this document when preparing changes or reviewing pull requests.

## Important Notes
- **You must adhere to architectural guidelines when making changes.** See `ARCHITECTURE.md` for details on the architectural design and principles.
- **DO NOT change the `ARCHITECTURE.md` file!** It contains 31 architectural decisions that define the framework.
- Refer to `CONTRIBUTING.md` for general contribution guidelines.
- The project is pre-alpha; remove unused code rather than keeping backward compatibility.  Actively remove deprecated, unused, or legacy code when adding new features.
- Prefer adding `TODO:` comments when scope is unclear.
- Create `AGENT NOTE:` comments for other agents.
- Always use the Poetry environment for development.
- Run `poetry install --with dev` before executing any quality checks or tests.
- Run tests using `poetry run poe test` or related tasks to ensure `PYTHONPATH` is set.

## Code Review Checklist

When reviewing pull requests, verify compliance with architectural decisions in this order:

### 🚨 Critical Architectural Violations (Must Fix)

**1. 4-Layer Resource Architecture (Decision #1)**
- [ ] Infrastructure plugins have no dependencies
- [ ] Resource interfaces depend only on infrastructure
- [ ] Canonical resources depend only on resource interfaces
- [ ] Custom resources depend only on canonical resources
- [ ] No circular dependencies across layers

**2. Plugin Import Restrictions (Decision #1)**
- [ ] Plugins do NOT import core modules directly
- [ ] Only allowed: plugin base classes, resource interfaces, utilities
- [ ] Core modules may import plugins (one-way dependency)

**3. Stage Assignment Rules (Decision #4)**
- [ ] Uses precedence: Config override → Class default → THINK fallback
- [ ] No magic stage inference from source code
- [ ] Pipeline stages: INPUT → PARSE → THINK → DO → REVIEW → OUTPUT

**4. Response Termination Control (Decision #7)**
- [ ] Only OUTPUT stage plugins call `context.say()`
- [ ] Other stages use `context.think()` for intermediate results
- [ ] Pipeline loops until OUTPUT plugin terminates with response

**5. Stateless Worker Architecture (Decision #6)**
- [ ] No conversation state in worker instance variables
- [ ] All user data persisted externally via Memory resource
- [ ] Workers load/save state per request
- [ ] Any worker can handle any user request

### ⚠️ Important Architectural Patterns (Should Fix)

**6. State Management Dual Interface (Decision #23)**
- [ ] Simple cases use anthropomorphic methods: `remember()`, `recall()`, `think()`, `reflect()`
- [ ] Complex cases use Memory resource directly: `query()`, `vector_search()`
- [ ] All data persisted externally, not in memory

**7. Dependency Injection Pattern (Decision #11)**
- [ ] Resources declare `dependencies = ["memory", "llm"]`
- [ ] Container injects dependencies as attributes post-construction
- [ ] No constructor-based dependency passing

**8. Progressive Disclosure (Decision #2)**
- [ ] Layer 0: Zero-config decorators work (`@agent.tool`)
- [ ] Layer 1: Function decorators with auto-classification
- [ ] Layer 2: Class-based plugins with explicit control
- [ ] Layer 3: Advanced plugins with sophisticated access

**9. Fail-Fast Error Handling (Decisions #5, #15)**
- [ ] Plugin failure immediately terminates stage
- [ ] Failed stage triggers ERROR stage processing
- [ ] No cascading partial failures

### ✅ Beneficial Patterns (Nice to Have)

**10. Configuration Validation (Decision #18)**
- [ ] Uses Pydantic models exclusively
- [ ] Clear field-specific error messages
- [ ] Type coercion for common mistakes

**11. Multi-User Support (Decision #29)**
- [ ] Functions accept `user_id` parameter
- [ ] Automatic conversation namespacing: `{user_id}_{pipeline_id}`
- [ ] Memory isolation: `{user_id}:{key}`

## Architecture Quick Reference

### Core Foundational Architecture

**Decision #1: 4-Layer Resource Architecture**
```python
# ✅ GOOD: Proper layer separation
class PostgresInfrastructure(InfrastructurePlugin):  # Layer 1
    infrastructure_type = "database"

class DatabaseResource(ResourcePlugin):  # Layer 2
    infrastructure_dependencies = ["database"]

class Memory(AgentResource):  # Layer 3
    def __init__(self, database: DatabaseResource, vector_store: VectorStoreResource):
        pass

class SmartMemory(AgentResource):  # Layer 4
    def __init__(self, memory: Memory, llm: LLM):
        pass

# ❌ BAD: Layer violation
class Memory(AgentResource):  # Layer 3
    def __init__(self, postgres: PostgresInfrastructure):  # Skips Layer 2
        pass
```

Custom resources without dependencies may optionally be placed in **Layer 3**.

**Decision #4: Stage Assignment Precedence**
```python
# ✅ GOOD: Explicit stage assignment
class WeatherPlugin(ToolPlugin):
    stage = DO  # Class default

# Config override (highest precedence)
plugins:
  weather:
    type: WeatherPlugin
    stage: REVIEW  # Overrides class default

# ❌ BAD: Magic stage inference
class WeatherPlugin(ToolPlugin):
    # No stage declared - relies on source code analysis
    pass
```

**Decision #7: Response Termination Control**
```python
# ✅ GOOD: Only OUTPUT stage sets response
class ThinkingPlugin(PromptPlugin):
    stage = THINK
    
    async def _execute_impl(self, context):
        await context.think("analysis", "my analysis")  # Store for later

class OutputPlugin(PromptPlugin):
    stage = OUTPUT
    
    async def _execute_impl(self, context):
        analysis = await context.reflect("analysis")
        await context.say(f"Final response: {analysis}")  # Terminates pipeline

# ❌ BAD: Non-OUTPUT stage setting response
class ThinkingPlugin(PromptPlugin):
    stage = THINK
    
    async def _execute_impl(self, context):
        await context.say("Early response")  # VIOLATION: Wrong stage
```

### Core Pipeline Architecture

**Decision #23: State Management Dual Interface**
```python
# ✅ GOOD: Anthropomorphic for simple cases
async def simple_plugin(context):
    user_prefs = await context.recall("preferences", {})
    await context.remember("last_topic", "weather")
    await context.think("analysis", "processing")

# ✅ GOOD: Memory resource for complex cases
async def complex_plugin(context):
    memory = context.get_resource("memory")
    results = await memory.query("SELECT * FROM conversations WHERE...")
    similar = await memory.vector_search("user question", k=5)

# ❌ BAD: Using wrong interface for complexity level
async def simple_plugin(context):
    memory = context.get_resource("memory")
    # Complex SQL for simple key-value storage
    await memory.query("INSERT INTO kv_store VALUES (?, ?)", ["key", "value"])
```

**Decision #6: Stateless Workers**
```python
# ✅ GOOD: External state persistence
class PipelineWorker:
    def __init__(self, registries):
        self.registries = registries  # Shared resources only
        # No conversation data in instance variables
    
    async def execute(self, pipeline_id, message):
        # Load state from external storage
        memory = self.registries.resources.get("memory")
        conversation = await memory.load_conversation(pipeline_id)
        
        # Process with ephemeral state
        state = PipelineState(conversation=conversation)
        result = await self.run_pipeline(state)
        
        # Persist back to external storage
        await memory.save_conversation(pipeline_id, state.conversation)

# ❌ BAD: Worker holds conversation state
class PipelineWorker:
    def __init__(self):
        self.conversations = {}  # VIOLATION: State in worker
        self.user_data = {}      # VIOLATION: State in worker
```

### Common Anti-Patterns to Catch

**Plugin Import Violations**
```python
# ❌ BAD: Plugin importing core modules
from entity.core.pipeline import Pipeline  # VIOLATION
from entity.core.agent import Agent        # VIOLATION

class MyPlugin(PromptPlugin):
    def __init__(self):
        self.pipeline = Pipeline()  # VIOLATION

# ✅ GOOD: Plugin using allowed imports
from entity.plugins.base import PromptPlugin  # Allowed
from entity.resources.memory import Memory   # Allowed
```

**Stage Assignment Violations**
```python
# ❌ BAD: Magic stage inference
@some_decorator_that_infers_stages
def my_function():
    pass

# ❌ BAD: Complex precedence rules
class MyPlugin(PromptPlugin):
    priority = 5  # VIOLATION: No priority system
    inferred_stage = "auto"  # VIOLATION: No inference
```

**Response Control Violations**
```python
# ❌ BAD: Early pipeline termination
class ParsePlugin(PromptPlugin):
    stage = PARSE
    
    async def _execute_impl(self, context):
        if simple_case:
            await context.say("Quick answer")  # VIOLATION: Wrong stage
```

## Architecture Reference

### 31 Architectural Decisions by Priority

**Core Foundational (Must Understand):**
- Decision #1: 4-Layer Resource Architecture
- Decision #6: Stateless Workers with External State
- Decision #4: Plugin Stage Assignment Rules
- Decision #23: State Management Dual Interface
- Decision #7: Response Termination Control
- Decision #8: Stage Results Accumulation

**Core Resource Management:**
- Decision #10: Memory Resource Consolidation
- Decision #3: Core Canonical + Flexible Keys
- Decision #11: Resource Dependency Injection
- Decision #13: Resource Lifecycle Management

**Developer Experience & API Design:**
- Decision #24: Single Agent Class Pattern
- Decision #27: Layer 0 Zero-Config Experience
- Decision #2: Progressive Disclosure (3-Layer Plugin System)
- Decision #22: Explicit Configuration with Smart Defaults

**Error Handling & Validation:**
- Decision #5: Fail-Fast with Multi-Layered Validation
- Decision #15: Error Handling and Failure Propagation
- Decision #18: Pydantic Configuration Validation

**[Continue with remaining decisions...]**

### Finding Architectural Details

To find specific architectural decision details:

```bash
grep '^## <NUM>\. ' ARCHITECTURE.md
```

Where `<NUM>` is the decision number (e.g., `## 1. Core Mental Model`).

### Review Commands

Before approving any PR, verify architectural compliance:

```bash
# Code quality checks
poetry run black src tests
poetry run ruff check --fix src tests
poetry run mypy src
poetry run bandit -r src
poetry run vulture src tests
poetry run unimport --remove-all src tests

# Configuration validation
poetry run entity-cli --config config/dev.yaml verify
poetry run entity-cli --config config/prod.yaml verify
poetry run python -m src.entity.core.registry_validator

# Test architectural boundaries
poetry run poe test-architecture
poetry run poe test-plugins
poetry run poe test-resources
```

## Review Decision Tree

When reviewing code changes:

1. **Does it add new plugins?** → Check 4-layer architecture, import restrictions, stage assignment
2. **Does it modify resources?** → Check dependency injection, lifecycle management, external persistence
3. **Does it change pipeline flow?** → Check stage assignment, response termination, state management
4. **Does it add configuration?** → Check Pydantic validation, hot-reload scope, explicit patterns
5. **Does it handle errors?** → Check fail-fast behavior, ERROR stage processing
6. **Does it support multiple users?** → Check user_id parameter, conversation namespacing

Always verify that changes maintain the core architectural principles while advancing the framework's capabilities.
