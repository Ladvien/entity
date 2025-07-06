def __getattr__(name: str):
    if name == "CacheResource":
        from user_plugins.resources import CacheResource

        return CacheResource
    if name == "DuckDBVectorStore":
        from plugins.builtin.resources.duckdb_vector_store import \
            DuckDBVectorStore

        return DuckDBVectorStore
    if name == "LocalFileSystemResource":
        from plugins.builtin.resources.local_filesystem import \
            LocalFileSystemResource

        return LocalFileSystemResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "CacheResource",
    "DuckDBVectorStore",
    "LocalFileSystemResource",
]
