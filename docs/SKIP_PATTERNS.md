# Pipeline Skip Patterns and Best Practices

## Overview

Entity's pipeline optimization feature allows plugins to conditionally skip execution and entire stages to be bypassed when not needed. This reduces latency for simple queries and improves overall system performance.

## Core Concepts

### Plugin-Level Skipping

Plugins can declare whether they should execute based on the current context using two methods:

1. **Skip Conditions**: Declarative conditions that determine when to skip
2. **Custom should_execute()**: Override method for complex logic

### Stage-Level Skipping

Stages are automatically skipped when:
- No plugins in the stage will execute
- Stage dependencies have not been skipped
- The stage is not marked as required (OUTPUT and ERROR are always required)

## Implementation Patterns

### 1. Simple Skip Conditions

```python
class OptionalPlugin(Plugin):
    """Plugin that skips for short messages."""

    skip_conditions = [
        lambda ctx: len(ctx.message) < 10,  # Skip short messages
        lambda ctx: ctx.user_id == "bot",   # Skip bot users
    ]
```

### 2. Configuration-Based Skipping

```python
class ConditionalPlugin(Plugin):
    """Plugin with configurable skip behavior."""

    class ConfigModel(BaseModel):
        enabled: bool = True
        min_message_length: int = 20
        allowed_users: List[str] = []

    def __init__(self, resources, config):
        super().__init__(resources, config)

        # Set skip conditions based on config
        self.skip_conditions = [
            lambda ctx: not self.config.enabled,
            lambda ctx: len(ctx.message) < self.config.min_message_length,
            lambda ctx: (
                self.config.allowed_users and
                ctx.user_id not in self.config.allowed_users
            ),
        ]
```

### 3. Context-Aware Skipping

```python
class SmartPlugin(Plugin):
    """Plugin that skips based on previous stage results."""

    def should_execute(self, context: PluginContext) -> bool:
        # Check parent class conditions first
        if not super().should_execute(context):
            return False

        # Skip if previous stage was skipped
        if context.current_stage in context.skipped_stages:
            return False

        # Skip if specific plugin already ran
        if "parse.NLPPlugin" in context.skipped_plugins:
            return False

        # Check message content
        if "skip me" in context.message.lower():
            return False

        return True
```

### 4. Performance-Based Skipping

```python
class ExpensivePlugin(Plugin):
    """Plugin that skips under high load."""

    def should_execute(self, context: PluginContext) -> bool:
        # Skip if system is under high load
        metrics = context.get_resource("metrics")
        if metrics and metrics.get_load() > 0.8:
            return False

        # Skip if user has made too many requests
        rate_limiter = context.get_resource("rate_limiter")
        if rate_limiter and rate_limiter.is_limited(context.user_id):
            return False

        return super().should_execute(context)
```

## Best Practices

### 1. Keep Skip Logic Simple

Skip conditions should be fast and deterministic. Avoid:
- Database queries
- Network calls
- Complex computations
- Random decisions

### 2. Respect Stage Dependencies

Always consider how skipping affects downstream stages:

```python
# Good: Check dependencies
def should_execute(self, context):
    # Don't skip if later stages depend on our output
    if self.assigned_stage == WorkflowExecutor.PARSE:
        # THINK and DO stages often need parsed data
        return True
    return super().should_execute(context)

# Bad: Skip without considering dependencies
def should_execute(self, context):
    return random.random() > 0.5  # Don't do this!
```

### 3. Use Metrics for Monitoring

Track skip patterns to optimize performance:

```python
class MonitoredPlugin(Plugin):
    """Plugin that tracks its skip rate."""

    async def _execute_impl(self, context):
        # Track execution
        await context.log(
            LogLevel.DEBUG,
            LogCategory.PERFORMANCE,
            f"Plugin {self.__class__.__name__} executed"
        )
        # ... plugin logic ...

    def should_execute(self, context):
        should_run = super().should_execute(context)

        if not should_run:
            # Track skip
            context.log(
                LogLevel.DEBUG,
                LogCategory.PERFORMANCE,
                f"Plugin {self.__class__.__name__} skipped",
                reason=self._get_skip_reason(context)
            )

        return should_run
```

### 4. Document Skip Conditions

Always document why a plugin might skip:

```python
class DocumentedPlugin(Plugin):
    """Plugin for processing complex queries.

    Skip Conditions:
    - Message length < 50 characters (too simple)
    - User is in trial mode (premium feature)
    - Previous cache hit (no processing needed)
    """

    skip_conditions = [
        lambda ctx: len(ctx.message) < 50,
        lambda ctx: ctx.recall("user_tier") == "trial",
        lambda ctx: ctx.recall(f"cache:{ctx.message}") is not None,
    ]
```

### 5. Test Skip Behavior

Write tests for both execution and skip scenarios:

```python
@pytest.mark.asyncio
async def test_plugin_skips_short_messages():
    plugin = OptionalPlugin(resources, config)
    context = PluginContext(resources, "user123")

    # Should skip
    context.message = "Hi"
    assert not plugin.should_execute(context)

    # Should execute
    context.message = "This is a longer message that needs processing"
    assert plugin.should_execute(context)
```

## Stage Dependency Rules

The following dependencies are enforced:

| Stage  | Depends On | Can Skip If |
|--------|------------|-------------|
| INPUT  | None       | Never (first stage) |
| PARSE  | INPUT      | INPUT not skipped, no plugins to run |
| THINK  | INPUT, PARSE | Dependencies not skipped, no plugins to run |
| DO     | INPUT, PARSE | Dependencies not skipped, no plugins to run |
| REVIEW | INPUT, PARSE | Dependencies not skipped, no plugins to run |
| OUTPUT | INPUT      | Never (response generation) |
| ERROR  | None       | Never (error handling) |

## Performance Optimization Tips

### 1. Order Plugins by Skip Likelihood

Place plugins most likely to skip early in the stage:

```python
workflow = Workflow()
# Add plugins in order of skip likelihood
workflow.add_plugin(QuickSkipPlugin(), stage="parse")  # Skips 80% of time
workflow.add_plugin(MediumPlugin(), stage="parse")     # Skips 50% of time
workflow.add_plugin(AlwaysRunPlugin(), stage="parse")  # Never skips
```

### 2. Use Pipeline Analyzer

Analyze your pipeline for optimization opportunities:

```python
from entity.workflow.pipeline_analyzer import PipelineAnalyzer

analyzer = PipelineAnalyzer(workflow, executor)
result = analyzer.analyze(context)

print(f"Skippable stages: {result.skippable_stages}")
print(f"Estimated savings: {result.estimated_savings_ms}ms")

for hint in result.optimization_hints:
    print(f"{hint.hint_type}: {hint.reason} (impact: {hint.impact})")
```

### 3. Cache Expensive Operations

Use context memory to cache results:

```python
class CachedPlugin(Plugin):
    """Plugin that caches expensive computations."""

    async def _execute_impl(self, context):
        cache_key = f"result:{context.message}"

        # Check cache
        cached = await context.recall(cache_key)
        if cached:
            return cached

        # Expensive operation
        result = await self._expensive_computation(context.message)

        # Cache result
        await context.remember(cache_key, result)
        return result

    def should_execute(self, context):
        # Skip if already cached
        cache_key = f"result:{context.message}"
        if context.recall(cache_key):
            return False
        return super().should_execute(context)
```

## Metrics and Monitoring

Access skip metrics from the executor:

```python
# After execution
metrics = executor.get_skip_metrics()
print(f"Stages skipped: {metrics['stages_skipped']}")
print(f"Plugins skipped: {metrics['plugins_skipped']}")
print(f"Total stages run: {metrics['total_stages_run']}")
print(f"Total plugins run: {metrics['total_plugins_run']}")

# Calculate skip rate
skip_rate = metrics['plugins_skipped'] / (
    metrics['plugins_skipped'] + metrics['total_plugins_run']
)
print(f"Plugin skip rate: {skip_rate:.2%}")
```

## Common Pitfalls to Avoid

1. **Circular Dependencies**: Don't create skip conditions that depend on the output of the same stage
2. **Side Effects in Conditions**: Skip conditions should be pure functions without side effects
3. **Expensive Checks**: Keep skip checks lightweight - they run for every request
4. **Over-Skipping**: Don't skip so aggressively that functionality breaks
5. **Under-Logging**: Always log skips for debugging and monitoring

## Migration Guide

To migrate existing plugins to use skip patterns:

1. Identify conditional logic in `_execute_impl()`
2. Extract conditions to `skip_conditions` or `should_execute()`
3. Remove early returns from `_execute_impl()`
4. Add tests for skip scenarios
5. Monitor skip metrics in production

Example migration:

```python
# Before
class OldPlugin(Plugin):
    async def _execute_impl(self, context):
        if len(context.message) < 10:
            return context.message  # Early return

        # Process message
        return processed_message

# After
class NewPlugin(Plugin):
    skip_conditions = [
        lambda ctx: len(ctx.message) < 10
    ]

    async def _execute_impl(self, context):
        # Always process when executed
        return processed_message
```

## Debugging Skip Behavior

Enable debug logging to trace skip decisions:

```python
# In your configuration
logging:
  level: DEBUG
  categories:
    - SYSTEM
    - PERFORMANCE

# Skip events will be logged
# DEBUG [SYSTEM] Skipped plugin MyPlugin in stage parse
# DEBUG [SYSTEM] Skipped stage think - no active plugins
```

Use the Pipeline Analyzer to understand skip patterns:

```python
# Analyze without context (static analysis)
static_result = analyzer.analyze()

# Analyze with context (runtime analysis)
runtime_result = analyzer.analyze(context)

# Get skip recommendations
recommendations = analyzer.get_stage_skip_recommendations(context)
for stage, should_skip in recommendations.items():
    print(f"{stage}: {'skip' if should_skip else 'run'}")
```
