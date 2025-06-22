# 🧠 Entity Framework

**Modular, voice-enabled agent framework with memory and plugin support.**

---

## 📌 Overview

The Entity Framework is a developer-friendly platform for building multimodal, intelligent agents that feature:

- ✅ Centralized configuration via YAML
- ✅ Plugin system for custom tools
- ✅ Unified memory (chat + vector embeddings)
- ✅ Input/output adapter support (e.g., TTS, SST)

---

## 🗂️ Project Structure

```
.
├── cli.py                  # CLI entrypoint
├── config.yml             # Central config file
├── src/
│   ├── core/               # Service registry and lifecycle
│   ├── tools/              # Plugin tool system
│   ├── memory/             # Unified memory access (chat + vector)
│   ├── adapters/           # I/O adapters (TTS, SST, etc.)
│   └── agent/              # Agent logic (LLM wrapper, prompting)
├── README.md
├── pyproject.toml          # Poetry setup
```

---

## ⚙️ Configuration-Driven Setup

The system is driven entirely by a single `config.yml`. It defines:

- **Database**: PostgreSQL + PGVector setup
- **LLM**: Base model and tuning parameters (via Ollama or similar)
- **Adapters**: Voice and audio settings

Example:

```yaml
database:
  host: "192.168.1.104"
  name: "memory"
  username: "${DB_USERNAME}"
  password: "${DB_PASSWORD}"
  db_schema: "entity"

adapters:
  tts:
    base_url: "http://localhost:8888"
    voice_name: "bf_emma"
    output_format: "wav"

  sst:
    enabled: false  # planned
    service: "whisper"
```

The config is parsed once at startup and registered globally using the `ServiceRegistry`.

---

## 🧠 Unified Memory System

All memory operations (chat history + embeddings) are routed through a unified memory layer. It is:

- Backed by PostgreSQL + PGVector
- Thread-aware
- Accessible by the agent and all tools
- Configured via `config.yml`

Memory operations support:
- Top-N similarity queries
- Full interaction logging
- Filtering by thread or type

---

## 🔧 Plugin Tool Architecture

The plugin system allows developers to define **custom tools** that the agent can invoke automatically or manually. These tools are modular, easy to implement, and fully integrated with the memory system.

### 🔌 Plugin Directory

All custom tool plugins live in the top-level `plugins/` directory:

```
plugins/
├── my_custom_tool.py        # Add your tool here
├── another_tool.py
```

Each tool is a Python file that subclasses `BaseToolPlugin`, and is automatically discovered and loaded at runtime.

### 🧰 Writing a Tool

Create a new Python file under `src/tools/`, and define a subclass of `BaseToolPlugin`:

```python
# src/tools/my_tool.py
from src.tools.base_tool_plugin import BaseToolPlugin

class MyCustomTool(BaseToolPlugin):
    name = "my_custom_tool"
    description = "Returns a fixed response."

    def run(self, input: str) -> str:
        return "Here's your response!"
```

### 🔁 Memory Access

If your tool needs to access memory (e.g., for retrieving context or storing results), use the service registry:

```python
from src.core.registry import get_service
from src.memory.system import MemorySystem

class RecallTool(BaseToolPlugin):
    name = "recall_tool"

    def run(self, input: str) -> str:
        memory: MemorySystem = get_service("memory")
        results = memory.search(input, top_k=3)
        return "\n".join(r.content for r in results)
```

### ⚙️ Auto-Registration

All tools are automatically loaded and registered at startup by `ToolManager`. No manual registration needed — just place your file in `src/tools/` and follow the base class structure.

---

## 🔊 Adapter System

### ✅ Output Adapters
- **TTS (Text-to-Speech)** via REST-based services (e.g., Chatterbox, Kokoro)
- Controlled via the `adapters.tts` section of the config

### 🔜 Planned Input Adapters
- **SST (Speech-to-Text)**: Whisper or other audio recognition tools
- Aimed at enabling full voice interaction

Adapters live in `src/adapters/` and are injected at runtime.

---

## 🚀 Execution Modes

Start the FastAPI web service:

```bash
poetry run python cli.py server
```

Run the CLI chat interface:

```bash
poetry run python cli.py client
```

Run both locally:

```bash
poetry run python cli.py both
```

---

## 🧪 Developer Tips

- Add new tools in `src/tools/`
- Add new adapters in `src/adapters/`
- Modify LLM behavior via `src/agent/`
- Memory is shared, thread-safe, and searchable

---

## 📜 License

MIT — see `LICENSE` for details.


# Entity AI Agent - Code Consolidation Checklist

## 🔧 Configuration System Overhaul
- [X] **Merge database configs** - Combine `DataConfig` and `StorageConfig` into single `DataConfig`
- [X] **Eliminate PersonalityConfig** - Move personality fields directly into `EntityConfig`
- [X] **Simplify adapter configs** - Replace separate adapter classes with single `AdapterConfig` + type field
- [ ] **Merge audio configs** - Combine `AudioConfig` into `TTSConfig`
- [ ] **Reduce config classes** - Target 3-4 config classes instead of 10+
- [ ] **Update config.yml** - Adjust YAML structure to match simplified config classes
- [ ] **Test config loading** - Ensure all existing functionality still works

## 📊 Data Models Consolidation
- [ ] **Merge ChatInteraction and ChatResponse** - Create single model with different serialization methods
- [ ] **Combine AgentResult and ChatResponse** - Unify into one model with `.to_api_response()` method
- [ ] **Remove ConversationSummary** - Replace with on-demand generation methods
- [ ] **Simplify tool execution models** - Streamline `ToolExecutionRequest`/`ToolExecutionResponse`
- [ ] **Update all imports** - Fix references to consolidated models throughout codebase
- [ ] **Verify serialization** - Ensure API responses still work correctly

## 🗂️ Service Registry Elimination
- [ ] **Remove ServiceRegistry class** - Delete `src/core/registry.py`
- [ ] **Delete src/core/ directory** - Remove entire core module
- [ ] **Implement direct dependency injection** - Pass dependencies directly in FastAPI app
- [ ] **Update app.py lifespan** - Remove registry usage, use direct initialization
- [ ] **Fix all registry imports** - Replace `ServiceRegistry.get()` calls with direct dependencies
- [ ] **Update routes.py** - Pass dependencies directly to router factory

## 🧠 Memory System Simplification
- [ ] **Merge MemorySystem and MemoryRetriever** - Combine into single `MemoryManager` class
- [ ] **Remove SchemaAwarePGVector wrapper** - Use standard PGVector with proper schema setup
- [ ] **Eliminate MemoryContextBuilder** - Make it a method of `EntityAgent`
- [ ] **Simplify memory initialization** - Reduce custom PGVector setup complexity
- [ ] **Update agent.py** - Integrate simplified memory management
- [ ] **Test memory functionality** - Ensure vector search and storage still work

## 💻 CLI Interface Cleanup
- [ ] **Merge ChatInterface and EntityAPIClient** - Interface should handle its own HTTP calls
- [ ] **Simplify render.py** - Combine three render functions into one with options parameter
- [ ] **Remove duplicate config loading** - Load config once in CLI entry point
- [ ] **Streamline command handling** - Reduce command processing complexity
- [ ] **Update cli.py** - Integrate consolidated chat interface
- [ ] **Test all CLI commands** - Verify chat, history, memory search, etc. still work

## 🛠️ Tool System Streamlining
- [ ] **Remove BaseToolPlugin abstraction** - Use LangChain tools directly
- [ ] **Simplify ToolManager** - Remove complex registration system
- [ ] **Delete base_tool_plugin.py** - No longer needed with LangChain approach
- [ ] **Update plugin system** - Use standard LangChain tool patterns
- [ ] **Migrate existing tools** - Convert current plugins to simplified format
- [ ] **Test tool execution** - Ensure all tools still function correctly

## 🗃️ Database Layer Reduction
- [ ] **Remove src/db/models.py** - Use Pydantic models directly with SQLAlchemy
- [ ] **Simplify DatabaseConnection class** - Use standard SQLAlchemy async patterns
- [ ] **Remove global connection management** - Pass connections as dependencies
- [ ] **Update memory system** - Use simplified database access
- [ ] **Clean up connection.py** - Remove unnecessary abstraction layers
- [ ] **Test database operations** - Verify all CRUD operations still work

## 📁 File Structure Reorganization
- [ ] **Create new simplified structure** - Implement target file organization
- [ ] **Move consolidated code** - Relocate code to new simplified files
- [ ] **Update all imports** - Fix import statements throughout project
- [ ] **Remove empty directories** - Clean up unused folders
- [ ] **Update setup/requirements** - Ensure project still installs correctly

## ✅ Testing & Validation
- [ ] **Run full test suite** - Ensure no functionality is broken
- [ ] **Test API endpoints** - Verify all routes still work
- [ ] **Test CLI functionality** - Check chat, server, status commands
- [ ] **Test memory operations** - Verify vector search and storage
- [ ] **Test tool execution** - Ensure all plugins still function
- [ ] **Performance validation** - Check that simplification doesn't hurt performance
- [ ] **Documentation update** - Update README and docs to reflect changes

## 🎯 Success Metrics
- [ ] **~40% code reduction** - Measure lines of code before/after
- [ ] **Reduced complexity** - Fewer classes and abstractions
- [ ] **Maintained functionality** - All features still work
- [ ] **Improved maintainability** - Easier to understand and modify
- [ ] **Cleaner dependencies** - Simpler import structure

---

**Priority Order:**
1. Configuration System (highest impact)
2. Service Registry Elimination (removes complexity)
3. Data Models Consolidation (reduces duplication)
4. Memory System Simplification (architectural improvement)
5. CLI and Tool Systems (polish and cleanup)