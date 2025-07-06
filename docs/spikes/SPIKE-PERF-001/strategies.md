# SPIKE-PERF-001: Performance Techniques

## Summary
This spike explores ways to improve throughput when calling external LLM services. We reviewed async batching, Redis caching, concurrency patterns, and retry strategies.

## Async Batching
- Group multiple prompts into a single request when the backend supports it.
- Use `asyncio.gather` to send batches concurrently.
- Monitor response times to find an optimal batch size.

## Redis Caching
- Store past prompt/response pairs in Redis using a short TTL.
- Key format: hash of the prompt and parameters.
- Check cache before invoking the LLM to avoid repeated work.

## Concurrency Patterns
- Use `asyncio` tasks for I/O bound work.
- Leverage `asyncio.Semaphore` to limit in-flight requests.
- For CPU-bound tasks, delegate to a thread or process pool.

## Retry and Backoff
- Use exponential backoff with jitter to avoid thundering herd issues.
- The `tenacity` library provides convenient decorators for retry policies.
- Limit the total number of retries to keep failure handling predictable.

