# Entity AI Agent - Comprehensive Code Review

## Executive Summary

This is a sophisticated AI agent system with PostgreSQL vector memory, built using FastAPI, LangChain, and a modular architecture. The project shows good architectural thinking but has several critical issues that need addressing.

## Project Modules

- Agent System Web API: FastAPI-based web API for the AI agent.
- Vector Memory: PostgreSQL-based vector storage for AI agent memory.
- Chat Interface: CLI for interacting with the AI agent.
- Plugins: Extensible plugins system for adding functionalities.
- Configuration: YAML-based configuration management.
- Database Connection: PostgreSQL connection management.
- Tools: Various utility tools for the AI agent.
- Shared Models: Common data models used across the project.
- Storage: Base and PostgreSQL storage implementations.
- Testing: Unit tests for the fun fact tool.
- CLI: Command-line interface for the AI agent.
- Environment Variables: Example environment variable file for configuration.


## Project Structure
```sh
.
├── cli.py
├── config.yaml
├── env_example
├── LICENSE
├── main.py
├── plugins
│   └── fun_fact_tool.py
├── poetry.lock
├── pyproject.toml
├── README.md
├── src
│   ├── __init__.py
│   ├── cli
│   │   ├── chat_interface.py
│   │   └── client.py
│   ├── db
│   │   └── connection.py
│   ├── service
│   │   ├── agent.py
│   │   ├── app.py
│   │   ├── config.py
│   │   └── routes.py
│   ├── shared
│   │   └── models.py
│   ├── storage
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── postgres.py
│   └── tools
│       ├── memory.py
│       └── tools.py
└── test_fun_fact.py
```

# Entity Agent AI ⚙️

**A modular, vector‑memory enhanced AI agent with tool‑plugin support.**

Provides chat, API, CLI, and plugin tool modes using Ollama LLM, FastAPI, PostgreSQL, and LangChain.

---

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/Ladvien/entity.git
   cd entity
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure** via `config.yaml`:
   ```yaml
   server:
     host: "0.0.0.0"
     port: 8000
   ollama:
     base_url: "http://localhost:11434"
     model: "llama2"
     temperature: 0.7
   database:
     url: "postgresql+asyncpg://user:pass@localhost/dbname"
   tools:
     plugin_path: "./plugins"
     enabled:
       - fun_fact
       - weather_fetcher
   memory:
     vector_dim: 1536
     backend: "postgres"
   storage:
     init_on_startup: true
     history_table: "chat_history"
   logging:
     level: INFO
     format: "%(asctime)s %(levelname)s %(message)s"
   ```

4. **Run the server**
   ```bash
   python main.py server
   ```

5. **Chat via CLI**
   ```bash
   python main.py chat
   ```

6. **FastAPI docs**  
   Visit `http://<host>:<port>/docs` for auto-generated OpenAPI interface.

---

## 🔧 Features

| Feature         | Description |
|----------------|-------------|
| **Vector memory** | Stores embeddings for retrieval-enhanced conversations |
| **PostgreSQL storage** | Chat history with efficient upsert routing |
| **Plugin tools** | Extend via custom tools in `./plugins`, loaded based on `config.tools.enabled` |
| **Modular CLI/API** | `chat`, `server`, `both`, `simple`, `config` modes supported |
| **LangChain integration** | Uses `StructuredTool` with safe async-to-sync adapters |

---

## 🛠️ Plugin Tool System

- Implement tools by subclassing `BaseToolPlugin` in `./plugins`.
- Define `name`, `args_schema`, and `async def run(self, input_data)`.
- Example plugin:

  ```python
  from pydantic import BaseModel
  from src.tools.tools import BaseToolPlugin

  class FunFactInput(BaseModel):
      topic: str

  class FunFactTool(BaseToolPlugin):
      name = "fun_fact"
      description = "Returns a fun fact about a topic"
      args_schema = FunFactInput

      async def run(self, input_data: FunFactInput) -> str:
          return f"Did you know? {input_data.topic} facts are fascinating!"
  ```

- Only plugins listed in `config.tools.enabled` are loaded—others are skipped.

---

## ✅ Improvements & Maintenance

- **CLI modes supported**: `server`, `chat`, `both`, `simple`, `config`
- **Centralized DB connection** via `DatabaseConnection` and refactored `PostgresChatStorage`
- **Fixed duplicate models**: now using a single Pydantic `ChatInteraction`
- **Improved logging & error handling** across modules
- **Safe plugin loading** with error isolation and filtering
- **Async-to-sync adapter** rewritten to avoid excessive event-loop creation

---

## 🧪 Testing & Development Tips

- Add unit tests for `ToolManager`, storage logic, and agent routines.
- Use the `/docs` endpoint to interactively test API and plugins.
- Implement test plugins to validate loading and execution filtering.
- Run `python main.py simple` to confirm config and service initialization.

---

## 📘 Roadmap

- **🎯 Enhanced testing**: Unit and integration tests for all core components.
- **🧼 Better documentation**: Expanded plugin guides and configuration details.
- **📏 Health checks**: Add a `/health` endpoint for production readiness.
- **🧩 ORM storage option**: Consider SQLAlchemy models for storage layer.
- **🧠 Thread/agent UI**: Summaries per conversation thread with tracking.

---

## ❤️ Contributing

Contributions are welcome! Please:

1. **Fork** the repo  
2. **Create issues** for bug reports or feature requests  
3. **Submit PRs** with tests/documentation  

---

## 📄 License

MIT © Ladvien