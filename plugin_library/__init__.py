from importlib import import_module

# Use user_plugins as the actual implementation
_user_plugins = import_module("user_plugins")

# Expose attributes and submodules
__all__ = getattr(_user_plugins, "__all__", [])
__path__ = _user_plugins.__path__  # type: ignore[attr-defined]
globals().update(
    {
        name: getattr(_user_plugins, name)
        for name in dir(_user_plugins)
        if not name.startswith("_")
    }
)
