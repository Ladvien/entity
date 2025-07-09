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