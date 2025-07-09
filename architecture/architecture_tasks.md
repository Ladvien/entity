## Architectural Decisions not Reviewed
- Logging
- Docker


## Implementation Updates Required

### 1. Response Termination Control
- **Modify `PluginContext.set_response()`** - Add stage validation to only allow DELIVER plugins
- **Update pipeline loop logic** - Ensure only DELIVER stage responses terminate iteration
- **Add validation error** - Clear error message when non-DELIVER plugins try to set response

### 2. Stage Results Accumulation  
- **Rename methods in `PluginContext`**:
  - `set_stage_result()` → `store()`
  - `get_stage_result()` → `load()` 
  - `has_stage_result()` → `has()`
- **Update all plugin examples** in docs and templates
- **Update method documentation** and type hints

### 3. Tool Execution Patterns
- **Rename methods in `PluginContext`**:
  - `use_tool()` → `tool_use()`
  - `execute_tool()` → `queue_tool_use()`
- **Update all references** in plugins and documentation
- **Keep both execution patterns** with existing functionality

### 4. Memory Resource Consolidation
- **Create new unified `Memory` class** replacing SimpleMemoryResource, MemoryResource
- **Embed `ConversationHistory` as property** instead of separate component
- **Update memory resource imports** throughout codebase
- **Migrate existing memory configurations** to new structure
- **Remove old memory classes** after migration

### 5. Resource Dependency Injection
- **Update all resource classes** to use explicit `dependencies = [...]` declarations
- **Modify container injection logic** to set dependencies as attributes post-construction
- **Remove constructor-based dependency passing** from resource classes
- **Update configuration examples** to reflect dependency relationships

### 6. Plugin Stage Assignment Precedence
- **Implement strict precedence hierarchy** in plugin registration
- **Add validation warnings** for stage conflicts
- **Update `PluginAutoClassifier`** to respect precedence rules
- **Document stage assignment patterns** and common overrides

### 7. Resource Lifecycle Management
- **Implement strict sequential initialization** in `SystemInitializer`
- **Remove degraded mode handling** - fail fast on any resource failure
- **Add reverse-order shutdown** sequence in cleanup
- **Update health check logic** to fail immediately rather than remove resources

### 8. Configuration Hot-Reload Scope
- **Restrict hot-reload to parameter changes only** in `config_update.py`
- **Add validation** to reject topology changes during hot-reload
- **Update documentation** to clarify restart requirements for non-parameter changes
- **Remove complex plugin addition/removal hot-reload logic**

### 9. Error Handling and Failure Propagation
- **Ensure fail-fast behavior** in stage execution - any plugin failure terminates stage
- **Update stage execution logic** to immediately trigger ERROR stage on plugin failure
- **Document ERROR stage patterns** for graceful failure handling
- **Remove any best-effort continuation logic**

### 10. Pipeline State Management Strategy
- **Remove state checkpoint mechanisms** - eliminate `state_file` and `snapshots_dir` parameters
- **Add structured logging** for stage completion with full context
- **Clean up state serialization utilities** if no longer needed elsewhere
- **Update `execute_pipeline`** to remove file-based state persistence

### 11. Plugin Execution Order Simplification
- **Remove `priority` attribute** from all plugin base classes
- **Remove priority sorting logic** in `PluginRegistry` 
- **Update plugin registration** to use YAML/list order
- **Update plugin templates** to remove priority references
- **Update documentation** to emphasize execution order through configuration order