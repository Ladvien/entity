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
