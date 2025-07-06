# SPIKE-PERF-002: Memory Optimization and Concurrency Safety

## Summary
This spike captures approaches for reducing memory usage and ensuring safe concurrent tool execution within the Entity Pipeline.

## Memory Optimization Proposals
### 1. Limit Stage Results
`PipelineState` caps the number of stored stage results using `max_stage_results` to prevent unbounded growth.

### 2. Tool Result Caching
`ToolRegistry` supports caching results with a configurable TTL. Cached data avoids repeated computation and is purged automatically when expired.

### 3. Persistent Storage
`StorageResource` and the updated `MemoryResource` persist history and vectors to disk-backed stores. Offloading data reduces in-memory footprint during long runs.

## Concurrency Safety
### 1. Locked Registries
Both `ToolRegistry` and `PluginRegistry` guard modifications with `asyncio.Lock` to avoid race conditions when registering or looking up entries.

### 2. Controlled Parallelism
`execute_pending_tools` uses an `asyncio.Semaphore` based on `concurrency_limit` from configuration. This ensures only a fixed number of tools run simultaneously.

### 3. Configurable Limits
`EntityConfig` exposes `ToolRegistryConfig` allowing deployments to tune concurrency and cache expiration independently for development and production.

## Recommendation
Keep the current locking strategy and concurrency controls. Explore tuning `max_stage_results` and cache TTLs based on workload. Persist larger histories via `StorageResource` when memory pressure becomes noticeable.

