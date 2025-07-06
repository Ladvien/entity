# SPIKE-ERR-001: Error Handling and Resilience Patterns

## Summary
This document explores error handling in state machine libraries and examines circuit breaker packages that could be leveraged within the Entity pipeline.

## State Machine Libraries
Several Python libraries implement finite-state machines with built-in error handling strategies:

- **`transitions`** – Offers explicit state definitions and callbacks for state transitions. Errors are typically handled by raising exceptions in transition callbacks.
- **`automat`** – Focuses on declarative state machines where invalid events raise an `NoTransition` exception, making error states explicit.
- **`aiofsm`** – Provides asynchronous state machines. Failures in transition coroutines propagate as task exceptions, allowing callers to implement retries or circuit breakers.

These libraries favour raising clear exceptions when a transition fails. Most provide hooks or callbacks where custom recovery logic can be applied.

## Circuit Breaker Packages
Circuit breakers prevent cascading failures by short‑circuiting repeated attempts when a dependency is unhealthy.

- **`tenacity`** – Primarily a retry library but can be used to build circuit breakers by tracking failures and delay periods. The project already uses `RetryPolicy` and `CircuitBreaker` wrappers built on `tenacity`.
- **`pybreaker`** – A standalone circuit breaker implementation. It tracks failure counts and exposes hooks for logging or fallback behaviour. Example usage:

```python
import pybreaker

breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
async def fetch_data():
    ...
```

Both packages support asynchronous code and allow custom listeners to monitor open or closed states.

## Example Pattern
A simple pattern combines a retry policy with a circuit breaker:

```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
import pybreaker

retry = AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

@breaker
async def call_service():
    async for attempt in retry:
        with attempt:
            return await expensive_call()
```

This approach retries transient failures but stops calling `expensive_call` once the breaker opens.

## Recommendation
- Use explicit exception types in state transition callbacks to surface failure modes.
- Wrap external dependencies with a circuit breaker such as `pybreaker` or the existing `CircuitBreaker` in `pipeline.reliability`.
- Combine retries and circuit breaking to balance resiliency with fast failure reporting.
