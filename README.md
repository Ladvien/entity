# Entity Pipeline Framework Architecture Summary

When instantiated without a configuration file, ``Agent`` loads a basic set of
plugins so the pipeline can run out of the box:

- ``EchoLLMResource`` – minimal LLM resource that simply echoes prompts.
- ``MemoryResource`` – unified interface that delegates to an in-memory backend by default.
- ``SearchTool`` – wrapper around DuckDuckGo's search API.
- ``CalculatorTool`` – safe evaluator for arithmetic expressions.

These defaults allow ``Agent()`` to process messages without any external
configuration.

<!-- start quick_start -->
Get started quickly by installing the package and running an agent with a YAML
file:

```bash
pip install entity-pipeline
python src/cli.py --config config.yaml
```
<!-- end quick_start -->
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
      type: pipeline.plugins.resources.sqlite_storage:SQLiteStorage
      path: ./entity.db
      pool_min_size: 1
      pool_max_size: 5
```

For ephemeral sessions, an in-memory backend is available:

```yaml
plugins:
  resources:
    database:
      type: pipeline.plugins.resources.memory_storage:MemoryStorage
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
   - Memory = Database + Vector Store + File System
   - Matches how developers think about storage layers
   - Clear upgrade path from simple to complex

## Suggested Implementation

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class MemoryResource(ResourcePlugin):
    """Unified memory interface composing multiple storage backends."""
    
    stages = [PipelineStage.PARSE]
    name = "memory"
    
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
    def from_config(cls, config: Dict) -> "MemoryResource":
        """Create MemoryResource from YAML configuration."""
        # Allow both programmatic and config-based initialization
        db_config = config.get("database")
        if db_config:
            db_type = db_config.get("type", "postgres")
            if db_type == "postgres":
                db = PostgresDatabaseResource(db_config)
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
    memory:
      type: memory
      database:
        type: pipeline.plugins.resources.sqlite_storage:SQLiteStorageResource
        path: ./agent.db
```

### DuckDB Configuration
```yaml
plugins:
  resources:
    memory:
      type: memory
      database:
        type: pipeline.plugins.resources.duckdb_database:DuckDBDatabaseResource
        path: ./agent.duckdb
        history_table: chat_history
```

### Advanced Configuration
```yaml
plugins:
  resources:
    memory:
      type: memory
      database:
        type: pipeline.plugins.resources.postgres_database:PostgresDatabaseResource
        host: localhost
        name: agent_db
      vector_store:
        type: pipeline.plugins.resources.pg_vector_store:PgVectorStore
        dimensions: 768
        table: embeddings
      filesystem:
        type: pipeline.plugins.resources.s3_filesystem:S3FileSystem
        bucket: agent-files
        region: us-east-1
```

### Programmatic Configuration
```python
# Start simple
memory = MemoryResource(
    database=SQLiteDatabaseResource("./agent.db")
)

# Use DuckDB
duckdb_resource = DuckDBDatabaseResource({"path": "./agent.duckdb"})
memory_duckdb = MemoryResource(database=duckdb_resource)

# Evolve to complex
postgres = PostgresDatabaseResource(connection_str)
memory = MemoryResource(
    database=postgres,
    vector_store=PgVectorStore(postgres, dimensions=768),
    filesystem=S3FileSystem(bucket="agent-files")
)
```

### S3 File Storage
The `S3FileSystem` backend persists files in Amazon S3. Configure the
`bucket` and optional `region` keys under `filesystem`.

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
   postgres = PostgresDatabaseResource(config)
   vector_store = PgVectorStore(postgres)  # Reuses connection pool
   ```

3. **Provide Sensible Defaults**
   ```python
   # If no config provided, use SQLite + local filesystem
   memory = MemoryResource()  # Works out of the box
   ```

4. **Clear Migration Path**
   ```python
   # Easy to migrate data between backends
   await memory.migrate_to(new_memory)
   ```

## Benefits for Users

1. **Progressive Complexity**
   - Start with just `MemoryResource()` 
   - Add database when needed
   - Add vector search when ready
   - Add file storage for multimodal

2. **Clear Mental Model**
   - Memory = persistent storage for agent
   - Composed of familiar components
   - Each component optional

3. **Testability**
   - Easy to mock individual components
   - Can test with in-memory implementations
   - Clear interfaces for each backend

This composition pattern would significantly improve the framework's usability while maintaining its flexibility. It's a perfect example of "simple things simple, complex things possible."
<<<<<<< HEAD

## AWS Deployment

Use Terraform's Python SDK to provision AWS databases, storage, and compute resources. The [deployment guide](docs/source/deploy_aws.md) walks through a minimal setup on Amazon Web Services.

=======
>>>>>>> 7966420636c5eba71f9deaf1bc4b88c234ab703d
