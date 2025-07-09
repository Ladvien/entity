class BasePlugin:
    """Minimal base class for plugins."""

    def __init__(self, config=None):
        self.config = config or {}
