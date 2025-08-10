# Type-Safe Dependency Injection Migration Guide

## Overview

This guide helps you migrate existing plugins from string-based dependency injection to the new type-safe system using Python protocols and type hints.

## Benefits of Type-Safe Dependencies

- **Compile-time error detection**: Catch dependency issues during development
- **IDE autocomplete**: Full IntelliSense support for injected resources
- **Better documentation**: Self-documenting dependency requirements
- **Refactoring safety**: Type-safe refactoring across the codebase
- **Runtime validation**: Automatic validation of resource compatibility

## Migration Steps

### 1. Update Plugin Base Class

**Before (Old System):**
```python
from entity.plugins.base import Plugin

class MyPlugin(Plugin):
    dependencies = ["llm", "memory"]  # String-based

    def __init__(self, resources: dict[str, Any], config: dict[str, Any] | None = None):
        super().__init__(resources, config)
        # Manual resource access with no type safety
        self.llm = self.resources["llm"]  # No IDE support
        self.memory = self.resources["memory"]  # Runtime errors possible
```

**After (New Type-Safe System):**
```python
from entity.plugins.typed_base import TypedPlugin, LLMProtocol, MemoryProtocol

class MyPlugin(TypedPlugin):
    def __init__(
        self,
        resources: dict[str, Any],
        config: dict[str, Any] | None = None,
        *,  # Force keyword-only arguments for dependencies
        llm: LLMProtocol,  # Type-safe injection
        memory: MemoryProtocol,  # IDE autocomplete available
    ):
        super().__init__(resources, config)
        self.llm = llm  # Fully typed
        self.memory = memory  # Compile-time validation
```

### 2. Using Convenience Base Classes

For common dependency patterns, use convenience base classes:

```python
# For LLM-only plugins
from entity.plugins.typed_base import LLMPlugin

class MyLLMPlugin(LLMPlugin):
    # LLM dependency automatically injected
    async def _execute_impl(self, context):
        response = await self.llm.generate("Hello")  # Type-safe!
        return response

# For Memory-only plugins
from entity.plugins.typed_base import MemoryPlugin

class MyMemoryPlugin(MemoryPlugin):
    # Memory dependency automatically injected
    async def _execute_impl(self, context):
        await self.memory.store("key", "value")  # Type-safe!

# For plugins needing both LLM and Memory
from entity.plugins.typed_base import LLMMemoryPlugin

class MyLLMMemoryPlugin(LLMMemoryPlugin):
    # Both LLM and Memory dependencies automatically injected
    async def _execute_impl(self, context):
        response = await self.llm.generate("prompt")
        await self.memory.store("response", response)
        return response
```

### 3. Custom Protocol Definition

For custom resource types, define your own protocols:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class CustomResourceProtocol(Protocol):
    """Protocol for custom resource interfaces."""

    async def custom_method(self, data: str) -> dict:
        """Custom method signature."""
        ...

    def health_check(self) -> bool:
        """Health check method."""
        ...

# Use in plugin
class MyCustomPlugin(TypedPlugin):
    def __init__(
        self,
        resources: dict[str, Any],
        config: dict[str, Any] | None = None,
        *,
        custom_resource: CustomResourceProtocol,
    ):
        super().__init__(resources, config)
        self.custom_resource = custom_resource
```

### 4. Backward Compatibility

The new system maintains backward compatibility with existing string-based dependencies:

```python
class HybridPlugin(TypedPlugin):
    dependencies = ["old_resource"]  # Still works

    def __init__(
        self,
        resources: dict[str, Any],
        config: dict[str, Any] | None = None,
        *,
        llm: LLMProtocol,  # Type-safe
    ):
        super().__init__(resources, config)
        self.llm = llm
        # Old-style access still available
        self.old_resource = self.resources["old_resource"]
```

## Available Protocols

### Core Resource Protocols

```python
from entity.plugins.typed_base import (
    LLMProtocol,           # For LLM resources
    MemoryProtocol,        # For Memory resources
    DatabaseProtocol,      # For Database resources
    VectorStoreProtocol,   # For Vector Store resources
    LoggingProtocol,       # For Logging resources
)
```

### Protocol Methods

#### LLMProtocol
```python
async def generate(self, prompt: str) -> str: ...
def health_check(self) -> bool: ...
```

#### MemoryProtocol
```python
async def store(self, key: str, value: Any) -> None: ...
async def load(self, key: str, default: Any = None) -> Any: ...
def health_check(self) -> bool: ...
```

#### DatabaseProtocol
```python
def execute(self, query: str, *params: object) -> object: ...
def health_check(self) -> bool: ...
```

## Error Handling

### Type Mismatch Errors

```python
# Runtime error with clear message
RuntimeError: MyPlugin dependency validation failed:
Type mismatch for llm: expected LLMProtocol, got str
```

### Missing Dependency Errors

```python
# Runtime error with clear message
RuntimeError: MyPlugin dependency validation failed:
Missing dependency: memory
```

### IDE Integration

With type-safe dependencies, your IDE will provide:

- **Autocomplete**: Method suggestions for injected resources
- **Type checking**: Real-time error detection
- **Go-to-definition**: Navigate to protocol definitions
- **Refactoring support**: Safe renaming across the codebase

## Testing Type-Safe Plugins

### Creating Mock Resources

```python
from unittest.mock import AsyncMock, Mock
from entity.plugins.typed_base import LLMProtocol, MemoryProtocol

# Create typed mocks
class MockLLM:
    async def generate(self, prompt: str) -> str:
        return f"Mock response for: {prompt}"

    def health_check(self) -> bool:
        return True

class MockMemory:
    def __init__(self):
        self._storage = {}

    async def store(self, key: str, value: Any) -> None:
        self._storage[key] = value

    async def load(self, key: str, default: Any = None) -> Any:
        return self._storage.get(key, default)

    def health_check(self) -> bool:
        return True

# Verify protocol compatibility
assert isinstance(MockLLM(), LLMProtocol)
assert isinstance(MockMemory(), MemoryProtocol)

# Use in tests
resources = {
    "llm": MockLLM(),
    "memory": MockMemory(),
}
plugin = MyPlugin(resources, {})
```

### Type-Safe Test Assertions

```python
def test_plugin_dependencies():
    # Type checking ensures these will work
    assert isinstance(plugin.llm, LLMProtocol)
    assert isinstance(plugin.memory, MemoryProtocol)

    # IDE will provide autocomplete for these calls
    response = await plugin.llm.generate("test")
    await plugin.memory.store("key", response)
```

## MyPy Configuration

Add strict type checking to catch issues early:

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true

# Enable protocol checking
enable_incomplete_feature = ["Unpack"]
enable_error_code = ["truthy-bool", "redundant-expr"]
```

## Common Migration Patterns

### Pattern 1: Simple Resource Access
```python
# Before
class OldPlugin(Plugin):
    dependencies = ["llm"]

    async def _execute_impl(self, context):
        llm = self.resources["llm"]  # No type safety
        return await llm.generate(context.text)

# After
class NewPlugin(LLMPlugin):
    async def _execute_impl(self, context):
        # self.llm is automatically typed and injected
        return await self.llm.generate(context.text)
```

### Pattern 2: Multiple Dependencies
```python
# Before
class OldMultiPlugin(Plugin):
    dependencies = ["llm", "memory", "database"]

    async def _execute_impl(self, context):
        llm = self.resources["llm"]
        memory = self.resources["memory"]
        database = self.resources["database"]
        # Manual access, no type safety

# After
class NewMultiPlugin(TypedPlugin):
    def __init__(
        self,
        resources: dict[str, Any],
        config: dict[str, Any] | None = None,
        *,
        llm: LLMProtocol,
        memory: MemoryProtocol,
        database: DatabaseProtocol,
    ):
        super().__init__(resources, config)
        self.llm = llm
        self.memory = memory
        self.database = database

    async def _execute_impl(self, context):
        # All resources are typed and validated
        response = await self.llm.generate(context.text)
        await self.memory.store("response", response)
        result = self.database.execute("SELECT * FROM responses")
        return result
```

### Pattern 3: Optional Dependencies
```python
from typing import Optional

class PluginWithOptionalDeps(TypedPlugin):
    def __init__(
        self,
        resources: dict[str, Any],
        config: dict[str, Any] | None = None,
        *,
        llm: LLMProtocol,
        memory: Optional[MemoryProtocol] = None,  # Optional
    ):
        super().__init__(resources, config)
        self.llm = llm
        self.memory = memory

    async def _execute_impl(self, context):
        response = await self.llm.generate(context.text)

        # Safe optional access
        if self.memory:
            await self.memory.store("response", response)

        return response
```

## Best Practices

### 1. Use Type Annotations
Always provide type annotations for better IDE support:

```python
def __init__(
    self,
    resources: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    llm: LLMProtocol,  # Type annotation is crucial
    memory: MemoryProtocol,
):
```

### 2. Leverage IDE Features
- Enable type checking in your IDE
- Use autocomplete for resource methods
- Navigate to protocol definitions when needed

### 3. Create Custom Protocols
For domain-specific resources, create custom protocols:

```python
@runtime_checkable
class MLModelProtocol(Protocol):
    async def predict(self, features: list[float]) -> float: ...
    def load_model(self, path: str) -> None: ...
    def health_check(self) -> bool: ...
```

### 4. Test Protocol Compliance
Ensure your resources implement protocols correctly:

```python
def test_resource_protocol_compliance():
    resource = MyCustomResource()
    assert isinstance(resource, CustomProtocol)
```

## Troubleshooting

### Common Issues

**Issue**: `TypeError: Type mismatch for llm: expected LLMProtocol, got MockLLM`
**Solution**: Ensure your mock implements all protocol methods:

```python
class MockLLM:
    async def generate(self, prompt: str) -> str:
        return "mock"

    def health_check(self) -> bool:  # Don't forget this method!
        return True
```

**Issue**: `RuntimeError: Missing required dependency: memory`
**Solution**: Add the dependency to your resources dict:

```python
resources = {
    "llm": llm_resource,
    "memory": memory_resource,  # Add missing dependency
}
```

**Issue**: IDE not providing autocomplete
**Solution**: Check that:
1. Type annotations are present
2. Protocol imports are correct
3. IDE Python interpreter is set correctly

## Migration Checklist

- [ ] Replace `Plugin` with `TypedPlugin` or convenience base classes
- [ ] Add type annotations to `__init__` parameters
- [ ] Use keyword-only arguments (`*,`) for dependencies
- [ ] Remove manual resource access (`self.resources["name"]`)
- [ ] Update tests to use typed mocks
- [ ] Verify IDE autocomplete works
- [ ] Run mypy to check for type errors
- [ ] Test that dependency validation works as expected

## Support

For questions or issues with the migration:

1. Check this migration guide
2. Look at example plugins in the codebase
3. Refer to protocol definitions in `typed_base.py`
4. Run mypy for type checking validation
