# SPIKE-PERF-001: Pipeline Performance Benchmarks and Caching

## Summary
This spike documents benchmark results for the Entity Pipeline and recommends caching strategies to improve responsiveness.

## Benchmark Setup
- **Environment**: Ubuntu 22.04, Python 3.11
- **Hardware**: 8 vCPUs, 16 GB RAM
- **Dataset**: Synthetic conversations with 100 messages each
- **Command**: `pytest tests/performance -k benchmark -s`

## Results
| Scenario                 | Avg Runtime (s) | Peak Memory (MB) |
|--------------------------|-----------------|------------------|
| Cold start               | 12.4            | 320              |
| Warm start with cache    | 6.1             | 305              |

Caching parsed prompts and HTTP responses cut execution time by roughly 50% and reduced memory overhead by 5%.

## Recommendations
1. **Enable Disk Cache**: Use `pipeline.resources.sqlite_storage` for prompt and response caching. It persists between runs and is thread-safe.
2. **Cache LLM Responses**: Store LLM replies keyed by normalized prompts. This avoids redundant API calls during retries or repeated conversations.
3. **Use In-Memory Cache for Tests**: `pipeline.resources.in_memory_storage` speeds up unit tests and can be cleared between cases.
4. **Monitor Hit Rates**: Integrate metrics to track cache effectiveness. Adjust eviction policies based on hit/miss ratios.

## Next Steps
- Automate benchmark runs in CI for regressions.
- Document cache configuration options in the user guide.
