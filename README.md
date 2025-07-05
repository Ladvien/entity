# Entity Pipeline Framework Architecture Summary

When instantiated without a configuration file, ``Agent`` loads a basic set of
plugins so the pipeline can run out of the box:

- ``EchoLLMResource`` – minimal LLM resource that simply echoes prompts.
<<<<<< codex/update-docs-for-storageresource-plugin
- ``StorageResource`` – unified interface that composes database, vector store, and file system backends.
======
- ``MemoryResource`` – unified interface that delegates to an in-memory backend by default.
- ``StorageResource`` – composite layer combining database, vectors and files.
>>>>>> main
- ``SearchTool`` – wrapper around DuckDuckGo's search API.
- ``CalculatorTool`` – safe evaluator for arithmetic expressions.

These defaults allow ``Agent()`` to process messages without any external
configuration.

<!-- start quick_start -->
Get started quickly by installing dependencies with Poetry and running an agent
with a YAML file:

```bash
poetry install
poetry run python src/cli.py --config config.yaml
```
This project relies on `httpx==0.27.*`, which Poetry will install automatically.
<!-- end quick_start -->
## Environment Setup

1. Install Python 3.11+ and [Poetry](https://python-poetry.org/).
2. Run `poetry install` to create the virtual environment. This installs all
   dependencies, including `httpx==0.27.*`.
3. Start the agent with your desired configuration file.

For an infrastructure walkthrough on Amazon Web Services, see the [AWS deployment guide](docs/source/deploy_aws.md).

<!-- start config -->
The ``llm`` resource now accepts a ``provider`` key. Choose from ``openai``,
``ollama``, ``gemini``, or ``claude``:

```yaml
plugins:
  resources:
    llm:
      provider: ollama  # openai, ollama, gemini, claude
      model: tinyllama
      base_url: "http://localhost:11434"
```
Lightweight deployments can use SQLite:

```yaml
plugins:
  resources:
    database:
      type: plugins.builtin.resources.sqlite_storage:SQLiteStorageResource
      path: ./entity.db
      pool_min_size: 1
      pool_max_size: 5
```

For ephemeral sessions, an in-memory backend is available:

```yaml
plugins:
  resources:
    database:
      type: plugins.builtin.resources.memory_storage:MemoryStorage
```

HTTP adapter configuration with authentication and rate limiting:

```yaml
plugins:
  adapters:
    http:
      type: plugins.builtin.adapters.http:HTTPAdapter
      auth_tokens:
        - ${HTTP_TOKEN}
      rate_limit:
        requests: 60
        interval: 60
      audit_log_path: logs/audit.log
```
<!-- end config -->

Every plugin executes with a ``PluginContext`` which grants controlled
access to resources, conversation history, and helper methods for calling
tools or LLMs. This context keeps plugin logic focused while the framework
handles state management. See the
[context guide](docs/source/context.md) for a detailed overview of its
methods and responsibilities.


To expose the agent over HTTP, build a FastAPI app that uses the agent:

```python
from fastapi import FastAPI
from app import create_app

agent = Agent(...)
app = create_app(agent)
```

## Design Principles in Action

- **Progressive Disclosure (1)**: `Agent()` works out of the box with helpful defaults.
- **Zero Configuration Default (3)**: Basic resources and tools require no YAML.
- **Fail-Fast Validation (15)**: `SystemInitializer` raises clear errors when dependencies are missing.
- **Intuitive Mental Models (21)**: Stages map directly to `Parse`, `Think`, `Do`, `Review`, `Deliver`, and `Error`.


```python
# Progressive Disclosure example
agent = Agent()
@agent.plugin
def hello(context):
    return "hello"
```

## Runtime Configuration Reload
Update plugin settings without restarting the agent.

```bash
python src/cli.py reload-config updated.yaml
```

See [ARCHITECTURE.md](ARCHITECTURE.md#%F0%9F%94%84-reconfigurable-agent-infrastructure) for details on dynamic reconfiguration.

### Using the "llm" Resource Key
Define your LLM once and share it across plugins:

```yaml
plugins:
  resources:
    llm:
      provider: openai
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
```


This is an excellent mental model! The composition pattern you're proposing aligns perfectly with the framework's design principles and would make memory management much more intuitive. Here are my thoughts:

## Strengths of This Approach

1. **Clear Separation of Concerns**
   - Each resource has a single, well-defined responsibility
   - Easy to understand what each component does
   - Follows the Single Responsibility Principle

2. **Flexible Composition**
   - Users can mix and match backends
   - Easy to swap implementations (Postgres → SQLite, S3 → local filesystem)
   - Supports gradual complexity (start with just DB, add vector store later)

3. **Intuitive Mental Model**
   - Storage = Database + Vector Store + File System
   - Matches how developers think about storage layers
   - Clear upgrade path from simple to complex

## Suggested Implementation

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class StorageResource(ResourcePlugin):
    """Unified storage interface composing multiple backends."""
    
    stages = [PipelineStage.PARSE]
    name = "storage"
    
    def __init__(
        self,
        database: Optional[DatabaseResource] = None,
        vector_store: Optional[VectorStoreResource] = None,
        filesystem: Optional[FileSystemResource] = None,
        config: Optional[Dict] = None
    ):
        super().__init__(config or {})
        self.database = database
        self.vector_store = vector_store
        self.filesystem = filesystem
        
    @classmethod
    def from_config(cls, config: Dict) -> "StorageResource":
        """Create StorageResource from YAML configuration."""
        # Allow both programmatic and config-based initialization
        db_config = config.get("database")
        if db_config:
            db_type = db_config.get("type", "postgres")
            if db_type == "postgres":
                db = PostgresResource(db_config)
            elif db_type == "sqlite":
                db = SQLiteDatabaseResource(db_config)
            else:
                db = None
        else:
            db = None
            
        # Similar for vector_store and filesystem
        return cls(database=db, vector_store=vector_store, filesystem=filesystem)
    
    async def save_conversation(self, conversation_id: str, entries: List[ConversationEntry]):
        """Save conversation history using the database backend."""
        if self.database:
            await self.database.save_history(conversation_id, entries)
    
    async def search_similar(self, query: str, k: int = 5) -> List[str]:
        """Semantic search using the vector store."""
        if self.vector_store:
            return await self.vector_store.query_similar(query, k)
        return []
    
    async def store_file(self, key: str, content: bytes) -> str:
        """Store a file using the filesystem backend."""
        if self.filesystem:
            return await self.filesystem.store(key, content)
        raise ValueError("No filesystem backend configured")
```

## Configuration Examples

### Simple Configuration
```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.sqlite_storage:SQLiteStorageResource
        path: ./agent.db
```

### DuckDB Configuration
```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.duckdb_database:DuckDBDatabaseResource
        path: ./agent.duckdb
        history_table: chat_history
```

### Advanced Configuration
```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.postgres:PostgresResource
        host: localhost
        name: agent_db
      vector_store:
        type: plugins.builtin.resources.pg_vector_store:PgVectorStore
        dimensions: 768
        table: embeddings
      filesystem:
        type: plugins.builtin.resources.s3_filesystem:S3FileSystem
        bucket: agent-files
        region: us-east-1
```
Full examples live in [`config/dev.yaml`](config/dev.yaml) and
[`config/prod.yaml`](config/prod.yaml). Each file includes a commented
`storage:` block showing how to wire up `StorageResource` with sample database,
vector store, and filesystem settings.

### Programmatic Configuration
```python
# Start simple
storage = StorageResource(
    database=SQLiteDatabaseResource("./agent.db")
)

# Use DuckDB
duckdb_resource = DuckDBDatabaseResource({"path": "./agent.duckdb"})
storage_duckdb = StorageResource(database=duckdb_resource)

# Evolve to complex
postgres = PostgresResource(connection_str)
storage = StorageResource(
    database=postgres,
    vector_store=PgVectorStore(postgres, dimensions=768),
    filesystem=S3FileSystem(bucket="agent-files")
)
```

### S3 File Storage
The `S3FileSystem` backend persists files in Amazon S3. Configure the
`bucket` and optional `region` keys under `filesystem`.

### StorageResource Example
Combine chat history storage with local file persistence:
```yaml
plugins:
  resources:
    storage:
      type: storage
      database:
        type: plugins.builtin.resources.sqlite_storage:SQLiteStorageResource
        path: ./agent.db
      filesystem:
        type: plugins.builtin.resources.local_filesystem:LocalFileSystemResource
        base_path: ./files
```

## Implementation Recommendations

1. **Create Abstract Base Classes**
   ```python
   class DatabaseResource(ABC):
       @abstractmethod
       async def save_history(self, conversation_id: str, entries: List[ConversationEntry]): ...
       
       @abstractmethod
       async def load_history(self, conversation_id: str) -> List[ConversationEntry]: ...
   
   class VectorStoreResource(ABC):
       @abstractmethod
       async def add_embedding(self, text: str, metadata: Dict = None): ...
       
       @abstractmethod
       async def query_similar(self, query: str, k: int) -> List[Dict]: ...
   ```

2. **Support Dependency Sharing**
   ```python
   # Vector store can reuse database connection
   postgres = PostgresResource(config)
   vector_store = PgVectorStore(postgres)  # Reuses connection pool
   ```

3. **Provide Sensible Defaults**
   ```python
   # If no config provided, use SQLite + local filesystem
   storage = StorageResource()  # Works out of the box
   ```

4. **Clear Migration Path**
   ```python
   # Easy to migrate data between backends
   await storage.migrate_to(new_storage)
   ```

## Benefits for Users

1. **Progressive Complexity**
   - Start with just `StorageResource()` 
   - Add database when needed
   - Add vector search when ready
   - Add file storage for multimodal

2. **Clear Mental Model**
   - Storage = persistent storage for agent
   - Composed of familiar components
   - Each component optional

3. **Testability**
   - Easy to mock individual components
   - Can test with in-memory implementations
   - Clear interfaces for each backend

This composition pattern would significantly improve the framework's usability while maintaining its flexibility. It's a perfect example of "simple things simple, complex things possible."

