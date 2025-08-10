# Entity Framework GPT-OSS Plugin Development - Jira Stories

## Epic: GPT-OSS Integration Suite for Entity Framework
*Leverage OpenAI's gpt-oss-20b unique capabilities within Entity's 6-stage pipeline architecture*

---

## Non-Functional Requirements

### Performance
- All plugins must maintain < 100ms overhead
- Support concurrent processing of multiple channels
- Implement caching for repeated reasoning patterns

### Security
- Sandbox all code execution
- Validate all tool inputs/outputs
- Implement rate limiting for expensive operations

### Monitoring
- Structured logging for all plugin operations
- Metrics collection for reasoning levels and tool usage
- Distributed tracing support

### Testing
- Unit tests with >80% coverage
- Integration tests with actual gpt-oss models
- Load tests for high-concurrency scenarios

---

## Dependencies

1. **openai-harmony** library for format handling
2. **gpt-oss** Python package for model interaction
3. **Docker** for Python tool containerization
4. **httpx** for browser tool implementation
5. Entity framework core components

## Success Metrics

- **Reasoning Quality**: 30% improvement in complex task completion
- **Performance**: < 2s average response time for medium reasoning
- **Tool Success Rate**: > 95% successful tool executions
- **Safety**: Zero harmful content exposure to end users
- **Developer Productivity**: 50% reduction in prompt engineering time

---

## 🔧 Framework Improvement Stories



### Story 13: SQL Injection Prevention
**Priority:** P0 - Critical
**Story Points:** 3
**Sprint:** 1

#### User Story
As a security engineer, I want Entity to be immune to SQL injection attacks, so that user input never compromises database integrity.

#### Description
Implement proper parameterization for all SQL operations, including table names through a safe registry system.

#### Acceptance Criteria
- [ ] Create table name registry with validation
- [ ] Implement parameterized queries for all operations
- [ ] Add SQL query logging for audit
- [ ] Create security test suite for injection attempts
- [ ] Document secure query patterns
- [ ] Add query sanitization middleware

#### Technical Implementation
```python
# src/entity/resources/secure_database.py
class SecureDatabaseResource(DatabaseResource):
    def __init__(self, infrastructure):
        super().__init__(infrastructure)
        self._table_registry = {}
        self._query_validator = SQLQueryValidator()

    def register_table(self, alias: str, table_name: str):
        """Register a table with validated name."""
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        self._table_registry[alias] = table_name

    def execute_safe(self, query_template: str, table_alias: str, *params):
        table_name = self._table_registry.get(table_alias)
        if not table_name:
            raise ValueError(f"Unregistered table alias: {table_alias}")
        # Use proper parameterization
        return self.execute(query_template.format(table=table_name), *params)
```

---

### Story 14: Optional Pipeline Stages
**Priority:** P1 - High
**Story Points:** 5
**Sprint:** 2

#### User Story
As a developer, I want to skip unnecessary pipeline stages for simple queries, so that I reduce latency for basic operations.

#### Description
Implement a mechanism for plugins to declare whether they should run based on context, allowing stages to be skipped dynamically.

#### Acceptance Criteria
- [ ] Add `should_execute()` method to Plugin base class
- [ ] Implement stage skipping in WorkflowExecutor
- [ ] Create pipeline analyzer for optimization hints
- [ ] Add metrics for skipped stages
- [ ] Document skip patterns and best practices
- [ ] Ensure stage dependencies are respected

#### Technical Implementation
```python
# src/entity/plugins/base.py
class Plugin(ABC):
    def should_execute(self, context: PluginContext) -> bool:
        """Determine if plugin should run for this context."""
        # Default implementation
        if hasattr(self, 'skip_conditions'):
            for condition in self.skip_conditions:
                if condition(context):
                    return False
        return True

# src/entity/workflow/executor.py
class WorkflowExecutor:
    async def _run_stage(self, stage, context, message, user_id):
        plugins = self.workflow.plugins_for(stage)

        # Filter plugins that should execute
        active_plugins = [
            p for p in plugins
            if p.should_execute(context)
        ]

        if not active_plugins and self._can_skip_stage(stage):
            context.skipped_stages.append(stage)
            return message
```

---

### Story 15: Type-Safe Dependency Injection
**Priority:** P1 - High
**Story Points:** 5
**Sprint:** 2

#### User Story
As a developer, I want compile-time type checking for plugin dependencies, so that I catch errors during development rather than runtime.

#### Description
Replace string-based dependency injection with a type-safe system using Python's type hints and protocols.

#### Acceptance Criteria
- [ ] Define Protocol classes for each resource type
- [ ] Use Generic types for plugin dependencies
- [ ] Add mypy configuration for strict checking
- [ ] Create dependency injection container
- [ ] Implement IDE autocomplete support
- [ ] Add migration guide for existing plugins

#### Technical Implementation
```python
# src/entity/plugins/typed_base.py
from typing import Protocol, TypeVar, Generic, get_type_hints

class LLMProtocol(Protocol):
    async def generate(self, prompt: str) -> str: ...

class MemoryProtocol(Protocol):
    async def store(self, key: str, value: Any) -> None: ...
    async def load(self, key: str, default: Any = None) -> Any: ...

T = TypeVar('T')

class TypedPlugin(ABC, Generic[T]):
    @classmethod
    def get_dependencies(cls) -> dict[str, type]:
        """Return type hints for dependencies."""
        return get_type_hints(cls.__init__)

    def __init__(self, llm: LLMProtocol, memory: MemoryProtocol):
        # Type-safe injection
        self.llm = llm
        self.memory = memory
```

---

### Story 16: Asynchronous Database Operations
**Priority:** P2 - Medium
**Story Points:** 5
**Sprint:** 3

#### User Story
As a performance engineer, I want all database operations to be truly asynchronous, so that we don't block the event loop.

#### Description
Replace synchronous database operations wrapped in `asyncio.to_thread` with proper async database drivers.

#### Acceptance Criteria
- [ ] Integrate aiosqlite or asyncpg for async operations
- [ ] Maintain backward compatibility with sync API
- [ ] Implement connection pooling
- [ ] Add query timeout configuration
- [ ] Create performance benchmarks
- [ ] Document async patterns

#### Technical Implementation
```python
# src/entity/infrastructure/async_duckdb_infra.py
import aiosqlite

class AsyncDuckDBInfrastructure(BaseInfrastructure):
    async def connect(self):
        """Return async connection context manager."""
        return aiosqlite.connect(self.file_path)

    async def execute_async(self, query: str, *params):
        async with await self.connect() as conn:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchall()
```

---

### Story 17: Request Batching System
**Priority:** P2 - Medium
**Story Points:** 8
**Sprint:** 3

#### User Story
As a platform engineer, I want Entity to batch multiple requests for efficient processing, so that we can handle high-throughput scenarios.

#### Description
Implement request batching for pipeline processing to improve throughput in high-concurrency scenarios.

#### Acceptance Criteria
- [ ] Create request queue with configurable batch size
- [ ] Implement adaptive batching based on load
- [ ] Add batch timeout to prevent starvation
- [ ] Support priority queuing
- [ ] Maintain request isolation in batches
- [ ] Add metrics for batch efficiency

#### Technical Implementation
```python
# src/entity/core/batch_executor.py
class BatchWorkflowExecutor(WorkflowExecutor):
    def __init__(self, resources, workflow, batch_size=10, batch_timeout=0.1):
        super().__init__(resources, workflow)
        self.batch_queue = asyncio.Queue()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout

    async def execute_batch(self, messages: list[tuple[str, str]]):
        """Execute multiple messages in a single pipeline pass."""
        contexts = [
            PluginContext(self.resources, user_id)
            for _, user_id in messages
        ]

        # Process stages in batch
        for stage in self._ORDER:
            contexts = await self._run_stage_batch(stage, contexts)
```

---

### Story 18: Memory Lifecycle Management
**Priority:** P2 - Medium
**Story Points:** 5
**Sprint:** 4

#### User Story
As a system administrator, I want automatic memory cleanup and garbage collection, so that the system doesn't leak memory over time.

#### Description
Implement comprehensive memory lifecycle management including TTL, garbage collection, and memory pressure handling.

#### Acceptance Criteria
- [ ] Add TTL support for memory entries
- [ ] Implement LRU eviction policy
- [ ] Create memory pressure monitoring
- [ ] Add manual garbage collection API
- [ ] Implement memory usage limits per user
- [ ] Add memory metrics and alerts

#### Technical Implementation
```python
# src/entity/resources/managed_memory.py
class ManagedMemory(Memory):
    def __init__(self, database, vector_store, max_memory_mb=1000):
        super().__init__(database, vector_store)
        self.max_memory_mb = max_memory_mb
        self._ttl_registry = {}
        self._access_times = {}

    async def store_with_ttl(self, key: str, value: Any, ttl_seconds: int):
        await self.store(key, value)
        self._ttl_registry[key] = time.time() + ttl_seconds
        asyncio.create_task(self._expire_after(key, ttl_seconds))

    async def _garbage_collect(self):
        """Run garbage collection based on memory pressure."""
        if await self._get_memory_usage() > self.max_memory_mb * 0.9:
            await self._evict_lru_entries()
```

---

### Story 19: Enhanced Error Context
**Priority:** P3 - Low
**Story Points:** 3
**Sprint:** 4

#### User Story
As a developer, I want rich error context when debugging issues, so that I can quickly identify and fix problems.

#### Description
Improve error handling with detailed context, stack traces, and debugging information.

#### Acceptance Criteria
- [ ] Add structured error types for each component
- [ ] Include plugin stack in error messages
- [ ] Add request ID tracking through pipeline
- [ ] Implement error recovery strategies
- [ ] Create error analysis tools
- [ ] Add error pattern detection

#### Technical Implementation
```python
# src/entity/core/errors.py
@dataclass
class PipelineError(Exception):
    stage: str
    plugin: str
    context: dict
    request_id: str
    user_id: str
    original_error: Exception

    def __str__(self):
        return (
            f"Pipeline error in {self.stage}.{self.plugin}\n"
            f"Request: {self.request_id}\n"
            f"User: {self.user_id}\n"
            f"Context: {json.dumps(self.context, indent=2)}\n"
            f"Original: {self.original_error}"
        )
```

---

### Story 20: Sandbox Security Hardening
**Priority:** P1 - High
**Story Points:** 8
**Sprint:** 5

#### User Story
As a security engineer, I want truly isolated sandbox execution, so that malicious code cannot escape or affect the system.

#### Description
Implement comprehensive sandboxing using containers or seccomp for true isolation.

#### Acceptance Criteria
- [ ] Implement Docker/gVisor based sandboxing
- [ ] Add seccomp-bpf filters for system calls
- [ ] Create resource usage monitoring
- [ ] Implement network isolation options
- [ ] Add filesystem isolation
- [ ] Create security audit logging

#### Technical Implementation
```python
# src/entity/tools/secure_sandbox.py
import docker

class SecureSandboxRunner(SandboxedToolRunner):
    def __init__(self, timeout=5.0, memory_mb=100):
        super().__init__(timeout, memory_mb)
        self.docker_client = docker.from_env()

    async def run(self, func, *args, **kwargs):
        # Create isolated container
        container = self.docker_client.containers.create(
            "entity-sandbox:latest",
            command=self._serialize_function(func, args, kwargs),
            mem_limit=f"{self.memory_mb}m",
            network_mode="none",
            read_only=True,
            security_opt=["no-new-privileges"],
        )

        try:
            container.start()
            result = await self._get_result(container, self.timeout)
            return self._deserialize_result(result)
        finally:
            container.remove(force=True)
```
