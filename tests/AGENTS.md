# Entity Framework: Agent Testing Guidance

## Core Testing Philosophy

**Real Components Only**: Tests must use actual infrastructure components. No mocks, dummies, fakes, or test doubles. If a component is unavailable, skip the test gracefully.

**Architecture Compliance**: All tests must reflect the 4-layer architecture and use the four canonical resources (LLM, Memory, FileStorage, Logging).

**Integration-First**: Prefer integration tests that exercise multiple layers together over isolated unit tests.

## Test Execution Philosophy

1. **Real Infrastructure**: Always use actual DuckDB files, real local storage, real LLM services
2. **Graceful Degradation**: Skip tests when real services unavailable, never fake them  
3. **Clean State**: Each test starts with fresh resources but uses real persistence mechanisms
4. **Full Stack**: Test complete flows from Layer 1 infrastructure through Layer 4 agents
5. **User Isolation**: Verify real multi-user data isolation using actual database namespacing
6. **Rich Integration**: Test Rich console output and logging in actual terminal contexts

This testing approach ensures our framework works with real components and infrastructure, giving us confidence that it will work correctly in production environments.

## Test Structure Standards

### Resource Setup Pattern

```python
@pytest.fixture
def real_resources(tmp_path):
    """Provide real canonical resources for testing."""
    # Layer 1 - Real infrastructure
    duckdb_infra = DuckDBInfrastructure(str(tmp_path / "test.duckdb"))
    local_storage_infra = LocalStorageInfrastructure(str(tmp_path / "storage"))
    
    # Try real vLLM, fallback to real Ollama, skip if neither available
    try:
        vllm_infra = VLLMInfrastructure(auto_detect_model=True)
        if not vllm_infra.health_check():
            raise InfrastructureError("vLLM not available")
        llm_infra = vllm_infra
    except Exception:
        try:
            ollama_infra = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
            if not ollama_infra.health_check():
                pytest.skip("No LLM infrastructure available")
            llm_infra = ollama_infra
        except Exception:
            pytest.skip("No LLM infrastructure available")
    
    # Layer 2 - Resource interfaces
    db_resource = DatabaseResource(duckdb_infra)
    vector_resource = VectorStoreResource(duckdb_infra)
    llm_resource = LLMResource(llm_infra)
    storage_resource = StorageResource(local_storage_infra)
    
    # Layer 3 - Canonical resources
    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "file_storage": FileStorage(storage_resource),
        "logging": RichConsoleLoggingResource(level=LogLevel.DEBUG)
    }
```

### Plugin Testing Pattern

```python
class TestMyPlugin:
    """Test plugin using real resources and workflow context."""
    
    @pytest.mark.asyncio
    async def test_plugin_execution(self, real_resources):
        """Test plugin with real infrastructure."""
        plugin = MyPlugin(real_resources)
        context = PluginContext(real_resources, user_id="test_user")
        context.current_stage = WorkflowExecutor.THINK
        context.message = "test input"
        
        result = await plugin.execute(context)
        
        # Verify actual behavior, not mocked responses
        assert result is not None
        # Verify persistent state was created
        stored_value = await context.recall("plugin_result")
        assert stored_value is not None
```

### Workflow Testing Pattern

```python
@pytest.mark.asyncio 
async def test_complete_workflow(real_resources):
    """Test full workflow with real components."""
    workflow_steps = {
        WorkflowExecutor.INPUT: [RealInputPlugin],
        WorkflowExecutor.THINK: [RealThinkingPlugin], 
        WorkflowExecutor.OUTPUT: [RealOutputPlugin]
    }
    
    executor = WorkflowExecutor(real_resources, workflow_steps)
    result = await executor.run("Hello world", user_id="test_user")
    
    # Verify actual end-to-end behavior
    assert result.startswith("Processed:")
    
    # Verify persistent state across workflow
    memory = real_resources["memory"]
    conversation = await memory.load("test_user:conversation", [])
    assert len(conversation) > 0
```

## Test Categories

### 1. Infrastructure Tests
Test Layer 1 components with real external dependencies:

```python
@pytest.mark.integration
async def test_vllm_infrastructure():
    """Test vLLM infrastructure with actual model."""
    infra = VLLMInfrastructure(auto_detect_model=True)
    
    if not infra.health_check():
        pytest.skip("vLLM not available")
    
    await infra.startup()
    try:
        response = await infra.generate("Hello")
        assert len(response) > 0
    finally:
        await infra.shutdown()

@pytest.mark.integration  
def test_duckdb_infrastructure(tmp_path):
    """Test DuckDB with real database operations."""
    db_path = tmp_path / "test.duckdb"
    infra = DuckDBInfrastructure(str(db_path))
    
    assert infra.health_check()
    
    with infra.connect() as conn:
        result = conn.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
```

### 2. Resource Tests
Test Layer 2 and Layer 3 resource composition:

```python
@pytest.mark.asyncio
async def test_memory_persistence(tmp_path):
    """Test memory with real DuckDB persistence."""
    duckdb_infra = DuckDBInfrastructure(str(tmp_path / "memory.duckdb"))
    db_resource = DatabaseResource(duckdb_infra)
    vector_resource = VectorStoreResource(duckdb_infra)
    
    memory = Memory(db_resource, vector_resource)
    
    # Test actual persistence
    await memory.store("test:key", {"data": "value"})
    retrieved = await memory.load("test:key")
    
    assert retrieved["data"] == "value"
    
    # Verify database file was created
    assert (tmp_path / "memory.duckdb").exists()
```

### 3. Plugin Integration Tests
Test plugins in realistic workflow scenarios:

```python
@pytest.mark.asyncio
async def test_plugin_workflow_integration(real_resources):
    """Test plugin behavior within actual workflow execution."""
    
    class TestWorkflowPlugin(PromptPlugin):
        stage = WorkflowExecutor.THINK
        
        async def _execute_impl(self, context):
            logger = context.get_resource("logging")
            llm = context.get_resource("llm")
            
            await logger.log(LogLevel.INFO, LogCategory.PLUGIN_LIFECYCLE, "Processing")
            
            # Use real LLM
            response = await llm.generate(f"Analyze: {context.message}")
            await context.remember("analysis", response)
            
            return context.message
    
    # Test in real workflow context
    workflow_steps = {WorkflowExecutor.THINK: [TestWorkflowPlugin]}
    executor = WorkflowExecutor(real_resources, workflow_steps)
    
    result = await executor.run("What is AI?", user_id="test_user")
    
    # Verify real LLM was used and state was persisted
    memory = real_resources["memory"]
    analysis = await memory.load("test_user:analysis")
    assert analysis is not None
    assert len(analysis) > 0
```

## Skip Patterns for Unavailable Services

```python
def requires_vllm():
    """Skip decorator for tests requiring vLLM."""
    try:
        infra = VLLMInfrastructure()
        available = infra.health_check()
    except Exception:
        available = False
    
    return pytest.mark.skipif(
        not available, 
        reason="vLLM infrastructure not available"
    )

def requires_ollama():
    """Skip decorator for tests requiring Ollama."""
    try:
        infra = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
        available = infra.health_check()
    except Exception:
        available = False
    
    return pytest.mark.skipif(
        not available,
        reason="Ollama infrastructure not available"  
    )

# Usage
@requires_vllm()
@pytest.mark.asyncio
async def test_vllm_specific_feature():
    """Test that only runs when vLLM is available."""
    pass
```

## Test Environment Configuration

```python
# conftest.py - NO MOCKING OR PATCHING
import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session")
def test_config():
    """Configure test environment without mocking."""
    # Use real temporary directories
    test_dir = Path("/tmp/entity_tests")
    test_dir.mkdir(exist_ok=True)
    
    # Set environment for real resource discovery
    os.environ.setdefault("ENTITY_DUCKDB_PATH", str(test_dir / "test.duckdb"))
    os.environ.setdefault("ENTITY_STORAGE_PATH", str(test_dir / "storage"))
    os.environ.setdefault("ENTITY_LOG_LEVEL", "debug")
    
    return {
        "test_dir": test_dir,
        "duckdb_path": test_dir / "test.duckdb",
        "storage_path": test_dir / "storage"
    }

@pytest.fixture(autouse=True)
def cleanup_test_data(test_config):
    """Clean up test data between tests."""
    yield
    # Clean up real files created during tests
    import shutil
    if test_config["test_dir"].exists():
        shutil.rmtree(test_config["test_dir"], ignore_errors=True)
```

## Performance and Load Testing

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_user_isolation(real_resources):
    """Test real multi-user scenarios with actual concurrency."""
    import asyncio
    
    async def user_workflow(user_id: str) -> str:
        executor = WorkflowExecutor(real_resources, default_workflow_steps)
        return await executor.run(f"Hello from {user_id}", user_id=user_id)
    
    # Run actual concurrent workflows
    tasks = [user_workflow(f"user_{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify isolation with real persistence
    memory = real_resources["memory"]
    for i in range(10):
        user_data = await memory.load(f"user_{i}:conversation")
        assert user_data is not None
        # Verify no data leakage between users
        other_users = [await memory.load(f"user_{j}:conversation") 
                      for j in range(10) if j != i]
        assert all(data != user_data for data in other_users if data)
```

## Prohibited Testing Patterns

❌ **Never Do This:**
```python
# NO MOCKING
@patch('entity.infrastructure.vllm_infra.VLLMInfrastructure')
def test_with_mock(mock_vllm):
    mock_vllm.return_value.generate.return_value = "fake response"
    # This violates our testing philosophy

# NO DUMMY CLASSES  
class DummyLLM:
    async def generate(self, prompt: str) -> str:
        return "dummy response"

# NO FAKE RESPONSES
def fake_health_check():
    return True
```

✅ **Do This Instead:**
```python
# REAL COMPONENTS WITH GRACEFUL SKIPPING
@pytest.mark.asyncio
async def test_llm_integration():
    try:
        llm_infra = VLLMInfrastructure(auto_detect_model=True)
        if not llm_infra.health_check():
            pytest.skip("vLLM not available")
        
        llm_resource = LLMResource(llm_infra)
        llm = LLM(llm_resource)
        
        # Test with real LLM
        response = await llm.generate("Hello")
        assert isinstance(response, str)
        assert len(response) > 0
        
    except Exception as e:
        pytest.skip(f"LLM infrastructure failed: {e}")
```

