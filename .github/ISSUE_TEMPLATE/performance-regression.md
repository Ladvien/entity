---
name: Performance Regression
about: Report performance issues after upgrading to v0.1.0+
title: '[PERF] Performance regression in v0.1.0+'
labels: 'performance, regression, priority-high'
assignees: ''
---

## Performance Regression Report

**Issue Summary:**
<!-- Brief description of the performance issue -->

**Regression Type:**
- [ ] Slower import times
- [ ] Increased memory usage
- [ ] Slower runtime performance
- [ ] Longer startup time
- [ ] Other: ________________

## Environment Details

**Entity Framework Versions:**
- Previous version (working):
- Current version (problematic):

**System Information:**
- OS: <!-- e.g., Ubuntu 20.04, macOS 13.0, Windows 11 -->
- Python version: <!-- python --version -->
- Architecture: <!-- e.g., x86_64, arm64 -->
- Available RAM:
- CPU:

**Installation Details:**
- [ ] Fresh installation of v0.1.0+
- [ ] Upgrade from previous version
- [ ] Using compatibility layer (old imports)
- [ ] Using new modular imports

## Performance Measurements

**Benchmarking method used:**
- [ ] Manual timing with time.time()
- [ ] Python's timeit module
- [ ] Entity's built-in benchmark script
- [ ] External profiling tools (specify): ________________

**Before (v0.0.12 or earlier):**
```
Import time: _____ seconds
Memory usage: _____ MB
Startup time: _____ seconds
Other metrics: ________________
```

**After (v0.1.0+):**
```
Import time: _____ seconds
Memory usage: _____ MB
Startup time: _____ seconds
Other metrics: ________________
```

**Regression magnitude:**
- [ ] <10% slower (minor)
- [ ] 10-25% slower (moderate)
- [ ] 25-50% slower (significant)
- [ ] >50% slower (critical)

## Code Reproduction

**Minimal reproduction code:**
```python
# Paste minimal code that demonstrates the regression
import time

start_time = time.time()
# Your code here
end_time = time.time()

print(f"Time taken: {end_time - start_time:.4f} seconds")
```

**Import patterns used:**
- [ ] Old imports (from entity.plugins.gpt_oss import ...)
- [ ] New imports (from entity_plugin_gpt_oss import ...)
- [ ] Mixed imports
- [ ] Core-only imports (no GPT-OSS)

## Profiling Data

**If you've done profiling, paste relevant output:**

**Python's cProfile:**
```
# Paste cProfile output if available
```

**Memory profiling:**
```
# Paste memory_profiler output if available
```

**Import timing (python -X importtime):**
```
# Paste importtime output if available
```

## Expected vs Actual Performance

**Expected performance:**
<!-- Based on our benchmarks or your v0.0.12 experience -->

**Actual performance:**
<!-- What you're observing -->

**Impact on your project:**
- [ ] Development workflow affected
- [ ] Production performance impacted
- [ ] CI/CD pipeline slowed down
- [ ] User experience degraded
- [ ] Other: ________________

## Troubleshooting Attempted

**Steps tried to resolve:**
- [ ] Cleared Python cache (__pycache__, .pyc files)
- [ ] Tested with fresh virtual environment
- [ ] Ran Entity's benchmark script
- [ ] Tested with different Python versions
- [ ] Compared old vs new import patterns
- [ ] Checked for competing processes/system load

**System resource check:**
- [ ] Adequate RAM available during test
- [ ] CPU not under heavy load during test
- [ ] Disk I/O not saturated during test
- [ ] Network not affecting package loading

## Workarounds

**Have you found any workarounds?**
<!-- Describe any temporary solutions -->

## Additional Context

**Project context:**
- Application type: <!-- CLI tool, web app, data processing, etc. -->
- Typical usage patterns:
- Performance requirements:
- Production impact severity:

**Comparison with our benchmarks:**
Our v0.1.0 benchmarks show:
- Entity import: ~0.0187s
- Plugin import: ~0.0736s
- GPT-OSS compat: ~0.0008s overhead

**How do your results compare?**

## Urgency Level

- [ ] Low - Minor slowdown, not affecting work
- [ ] Medium - Noticeable impact on development
- [ ] High - Significant impact on production
- [ ] Critical - Blocking deployment or causing outages

---

**Performance Resources:**
- [Performance Benchmarks](../benchmarks/import_performance_report.md)
- [Benchmark Script](../benchmarks/import_performance.py)
- [Migration Guide - Performance Section](../MIGRATION.md#performance)
- [Rollback Procedure](../ROLLBACK.md) (if critical)
