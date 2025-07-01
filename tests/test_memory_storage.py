import asyncio
from datetime import datetime

from pipeline.context import ConversationEntry
from pipeline.plugins.resources.memory_storage import MemoryStorage


def test_save_and_load_history():
    async def run():
        storage = MemoryStorage({"history_table": "tbl"})
        await storage.initialize()
        history = [
            ConversationEntry(
                content="hi", role="user", timestamp=datetime.now(), metadata={}
            ),
        ]
        await storage.save_history("1", history)
        loaded = await storage.load_history("1")
        return loaded

    loaded = asyncio.run(run())
    assert loaded[0].content == "hi"
