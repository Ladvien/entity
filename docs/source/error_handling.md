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
result = await execute_pipeline("hi", capabilities, state_logger=logger)
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

Base plugins include a simple circuit breaker using `failure_threshold` and `failure_reset_timeout` settings.

When any plugin raises an exception the framework stops executing the rest of that stage and no further stages run for that iteration.
The failure is captured in `FailureInfo` and the `ERROR` stage runs immediately
to handle the problem. No additional plugins from the failed stage are invoked.

## Error Responses and Failure Plugins

When a stage fails the pipeline records a `FailureInfo` object and runs plugins assigned to the `ERROR` stage. These plugins can attempt recovery, log the error or present a fallback message. A common pattern is to convert the failure info into a user-facing error response:

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


## ERROR Stage Patterns

When a plugin raises an exception the pipeline stops executing the remaining
plugins in that stage and immediately runs any plugins assigned to the `ERROR`
stage. These plugins typically log the issue or produce a fallback response.

```python
from pipeline.errors import create_static_error_response
from pipeline.stages import PipelineStage
from entity.core.plugins import FailurePlugin

class DefaultResponder(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        ctx.set_response(create_static_error_response(ctx.pipeline_id).to_dict())
```

```python
import logging

class BasicLogger(FailurePlugin):
    stages = [PipelineStage.ERROR]

    async def _execute_impl(self, ctx: PluginContext) -> None:
        info = ctx.get_failure_info()
        logging.error(
            "Stage %s plugin %s failed: %s",
            info.stage,
            info.plugin_name,
            info.error_message,
        )
```
