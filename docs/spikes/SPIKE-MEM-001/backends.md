# SPIKE-MEM-001: Storage and Vector Backends

## Summary
This spike documents the available database, vector store, and filesystem backends
found in `src/plugins/builtin/resources`. It also notes missing integrations such
as Pinecone and Google Cloud Storage.

## Database Resources
- `MemoryStorage` – in-memory conversation history.
- `SQLiteStorageResource` – SQLite persistence with async `aiosqlite`.
- `DuckDBDatabaseResource` – DuckDB backend with optional history table.
- `PostgresResource` – async Postgres with connection pooling and circuit breaker.

## Vector Store Resources
- `MemoryVectorStore` – keeps embeddings in a Python list.
- `DuckDBVectorStore` – uses DuckDB and `list_cosine_similarity` for queries.
- `PgVectorStore` – leverages `pgvector` extension in Postgres.

No Pinecone integration exists yet. `PgVectorStore` depends on the `vector` extension
being installed. The base interface is `VectorStoreResource` with `add_embedding`
and `query_similar` methods.

## Filesystem Resources
- `MemoryFileSystem` – simple in-memory dict for unit tests.
- `LocalFileSystemResource` – stores files under a configurable base path.
- `S3FileSystem` – uploads and retrieves objects via `aioboto3`.

The project lacks a Google Cloud Storage implementation, though one could mirror
the S3 approach using `google-cloud-storage`.

## Conclusions
Entity already includes local and cloud options for databases, vector stores, and
file storage. Adding Pinecone or GCS would require new resources adhering to the
existing `VectorStoreResource` or `FileSystemResource` contracts.
