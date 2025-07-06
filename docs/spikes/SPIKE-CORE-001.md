# SPIKE-CORE-001: Dependency Resolution Approaches

## Summary
This spike evaluates three approaches to resolving plugin dependencies within the Entity Pipeline. The current implementation relies on a `DependencyGraph` to calculate an execution order. We explored two alternative strategies and compared trade-offs.

## Resolution Strategies
### 1. Dependency Graph (Current)
- **Pros**
  - Automatically detects missing or circular dependencies.
  - Produces an explicit instantiation order.
  - Simple mental model via topological sort.
- **Cons**
  - Requires building the graph before any plugins can be instantiated.
  - Raises errors at startup rather than deferring to runtime.

### 2. Manual Ordering
- **Pros**
  - Minimal code complexity.
  - No upfront validation overhead.
- **Cons**
  - Relies on developers to maintain correct order.
  - Easy to introduce subtle bugs when adding new plugins.
  - Offers no automatic cycle detection.

### 3. Runtime Resolution
- **Pros**
  - Dependencies resolved lazily which can reduce startup time.
  - Flexible for dynamically loaded plugins.
- **Cons**
  - Increases runtime complexity and potential for late failures.
  - Harder to reason about ordering and error states.

## Dependency Graph
```python

@dataclass
class DependencyGraph:
    """Simple dependency graph with cycle detection."""

    graph: Dict[str, List[str]] = field(default_factory=dict)

    def _validate_missing(self) -> None:
        for node, deps in self.graph.items():
            for dep in deps:
                if dep not in self.graph:
                    available = list(self.graph)
                    raise SystemError(
                        f"Plugin '{node}' requires '{dep}' but it's not registered. "
                        f"Available: {available}"
                    )

    def topological_sort(self) -> List[str]:
        """Return nodes in dependency order or raise if a cycle exists."""
        self._validate_missing()

        in_degree: Dict[str, int] = {n: 0 for n in self.graph}
        for node, deps in self.graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue: List[str] = [n for n, d in in_degree.items() if d == 0]
        order: List[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for dep in self.graph[current]:
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        if len(order) != len(in_degree):
            cycle = [n for n in in_degree if n not in order]
            raise SystemError(f"Circular dependency detected involving: {cycle}")

        return order

```
The `DependencyGraph` class ensures all dependencies exist and returns a safe creation order.

## Prototype Results
Running a small script to sort a sample graph produced:
```
['A', 'B', 'C', 'D']
```
This confirms the graph returns `['A', 'B', 'C', 'D']` for a diamond dependency.

## Migration Effort
- **Manual Ordering** – Low effort: remove graph usage and document expected order. Each plugin file must be inspected and updated (~1 day).
- **Runtime Resolution** – Medium effort: refactor container logic to resolve dependencies on demand (~3-4 days) and add tests.
- **Dependency Graph** – Already implemented; no migration needed.

## Recommendation
Retain the current dependency graph approach. It balances clarity with safety and aligns with fail-fast principles.

## Next Steps
None required.
