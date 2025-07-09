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

## State Logging and Replay

Use `StateLogger` to capture pipeline state after each stage.

```python
logger = StateLogger("states.jsonl")
result = await execute_pipeline("hi", registries, state_logger=logger)
```

Replay logged transitions with `LogReplayer`:

```python
for transition in LogReplayer("states.jsonl").transitions():
    print(transition.stage, transition.pipeline_id)
```

## Reliability Helpers

`RetryPolicy` retries asynchronous calls with exponential backoff. `CircuitBreaker` wraps a call and prevents execution when failures exceed a threshold.

```python
policy = RetryPolicy(attempts=5, backoff=2.0)
result = await policy.execute(do_work)

breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
await breaker.call(do_work)
```

Tool plugins can define `max_retries` and `retry_delay` attributes (formerly
called `retry_attempts` and `retry_backoff`):

```python
class MyTool(ToolPlugin):
    max_retries = 2
    retry_delay = 0.5
```

Base plugins include a simple circuit breaker using `failure_threshold` and `failure_reset_timeout` settings.

## Error Responses and Failure Plugins

When a stage fails the pipeline records a `FailureInfo` object and runs plugins assigned to the `ERROR` stage. A failure plugin can inspect the info and set a response:

```python
from pipeline.errors.response import ErrorResponse

class ErrorFormatter(FailurePlugin):
    stages = [PipelineStage.DELIVER]
    async def _execute_impl(self, ctx: PluginContext) -> None:
        info = ctx.get_failure_info()
        ctx.set_response(
            ErrorResponse(
                error=info.error_message,
                message="Unable to process request",
            ).to_dict()
        )
```

Only plugins executed in the `DELIVER` stage may invoke ``set_response``.

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

If all retries fail the `DefaultResponder` plugin converts the captured `FailureInfo`
into an `ErrorResponse` and returns its `to_dict()` form via `create_error_response`.
