def __getattr__(name: str):
    if name == "CacheResource":
        from user_plugins.resources import CacheResource

        return CacheResource
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["CacheResource"]
