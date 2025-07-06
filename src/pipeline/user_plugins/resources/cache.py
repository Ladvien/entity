def __getattr__(name: str):
    if name == "CacheResource":
        from plugins.contrib.resources.cache import CacheResource

        return CacheResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["CacheResource"]
