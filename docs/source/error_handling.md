# Error Handling and Recovery

This guide explains how the Entity pipeline surfaces errors and restores state.

## `PipelineError` Hierarchy

All pipeline exceptions inherit from `PipelineError`. The key subclasses are:

```python
from pipeline.errors import (PipelineContextError, PipelineError,
                             PluginContextError, PluginExecutionError,
                             ResourceError, StageExecutionError,
                             ToolExecutionError)

```

`PluginExecutionError`, `ResourceError`, and `ToolExecutionError` indicate failures in plugins, resources, and tools. The context-aware classes carry additional fields like the stage and plugin name.

## StateManager Snapshots and Rollbacks

`PipelineState` supports snapshotting and restoration:

```python
state = PipelineState(...)
copy = state.snapshot()       # deep copy of current state
state.prompt = "new"
state.restore(copy)           # revert fields from snapshot
```

`experiments.state_manager.StateManager` persists snapshots for later retrieval:

```python
manager = StateManager(max_states=2)
await manager.save_state(state)       # stores a snapshot
saved = await manager.load_state(state.pipeline_id)
if saved:
    state.restore(saved)
```

## Reliability Helpers

`RetryPolicy` retries asynchronous calls with exponential backoff. `CircuitBreaker` wraps a call and prevents execution when failures exceed a threshold.

```python
policy = RetryPolicy(attempts=5, backoff=2.0)
result = await policy.execute(do_work)

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
await breaker.call(do_work)
```

Tool plugins can define `max_retries` and `retry_delay` attributes:

```python
class MyTool(ToolPlugin):
    max_retries = 2
    retry_delay = 0.5
```

Base plugins include a simple circuit breaker using `failure_threshold` and `failure_reset_timeout` settings.

## Error Responses and Failure Plugins

When a stage fails the pipeline records a `FailureInfo` object and runs plugins assigned to the `ERROR` stage. A failure plugin can inspect the info and set a response:

```python
class ErrorFormatter(FailurePlugin):
    stages = [PipelineStage.ERROR]
    async def _execute_impl(self, ctx: PluginContext) -> None:
        info = ctx.get_failure_info()
        ctx.set_response({"error": info.error_message})
```

If failure handling itself fails the framework returns a static response created by `create_static_error_response`:

```python
{
    "error": "System error occurred",
    "message": "An unexpected error prevented processing your request.",
    "error_id": "<pipeline id>",
    "timestamp": "<iso timestamp>",
    "type": "static_fallback",
}
```

Use `BasicLogger` and `ErrorFormatter` from `user_plugins.failure` as templates for custom failure handling.

## Error Recovery Strategies

Plugins can retry failures by specifying `max_retries` and `retry_delay` in their configuration. `BasePlugin` applies a `RetryPolicy` so `_execute_impl` is re-run before a failure is reported.

```python
class MyPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        ...

plugin = MyPlugin({"max_retries": 3, "retry_delay": 0.5})
```

If all retries fail the `DefaultResponder` plugin converts the captured `FailureInfo` into a JSON response using `create_error_response`.
