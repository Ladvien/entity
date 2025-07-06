# SPIKE-ERR-001: Circuit Breakers and State Recovery

## Summary
This spike investigates strategies for protecting the pipeline from repeated failures using circuit breakers and examines options for restoring state after an error. The goal is to keep failure handling simple while preventing data loss or endless retry loops.

## Circuit Breaker Options
### 1. Built-in Plugin Logic
- Each plugin tracks failures and open/close status in memory.
- Relies on the basic mechanism implemented in `BasePlugin`.
- **Pros**: No extra dependencies; fits the current code style.
- **Cons**: Hard to share failure counts across plugins. Only works within a single process.

### 2. `CircuitBreaker` Utility
- Provided in `pipeline.reliability.circuit_breaker` using `tenacity` for timing.
- Can wrap asynchronous calls and incorporate retry policies.
- **Pros**: Centralizes logic and decouples it from plugin implementations.
- **Cons**: Still local to one process; adds complexity when coordinating multiple breakers.

### 3. External Libraries
- Libraries like `pybreaker` offer advanced features such as listeners and persistent storage.
- **Pros**: Mature implementations with configurable states and monitoring hooks.
- **Cons**: Additional dependency management and potential overkill for simple pipelines.

## State Recovery Strategies
### 1. File Snapshots
- Current pipeline writes a JSON snapshot after each stage when `snapshots_dir` is provided.
- Allows reloading the last saved state via `PipelineState.from_dict`.
- **Pros**: Easy to implement and works without a database.
- **Cons**: Snapshots may be outdated if the process crashes before writing.

### 2. Persistent Store
- Save state in a database or object storage on each stage completion.
- **Pros**: Survives container restarts and enables distributed recovery.
- **Cons**: Requires schema management and increases latency.

### 3. In-Memory Checkpointing
- Keep a recent state copy in memory using `PipelineState.snapshot()` and restore with `restore()` if a plugin fails.
- **Pros**: Fastest recovery path for transient errors.
- **Cons**: Does not help when the process is terminated.

## Recommendation
Use the existing `CircuitBreaker` utility for all long-running or external calls. Pair it with file snapshots so failed pipelines can restart from the last completed stage. External libraries and persistent stores introduce more maintenance overhead than value at this stage.

## Risks
- File snapshots can accumulate and require cleanup.
- Per-process circuit breakers do not share state, so concurrent instances may trip independently.

## Next Steps
- Standardize snapshot cleanup in deployment scripts.
- Monitor breaker statistics to decide if shared storage is warranted later.
