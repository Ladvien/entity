from plugins.prompts.chat_history import ChatHistory

<<<<<<< HEAD:src/pipeline/plugins/prompts/chat_history.py
__all__ = ["ChatHistory"]
=======
from plugins.prompts.memory import MemoryPlugin


class ChatHistory(MemoryPlugin):
    """Alias for ``MemoryPlugin`` for backward compatibility."""

    pass
>>>>>>> 64d27a1aceba096733b70814249d0a84f4b3bce4:plugins/prompts/chat_history.py
